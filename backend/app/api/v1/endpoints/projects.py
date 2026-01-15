"""项目API端点"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.core.permissions import get_current_project_manager
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse
)
from app.services.project_service import ProjectService
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_project_manager)
):
    """创建项目（仅项目经理和管理员）"""
    try:
        project = ProjectService.create_project(db, project_data, current_user.id)
        return project
    except ValueError as e:
        raise ValidationError(str(e))


@router.get("/", response_model=ProjectListResponse)
async def get_projects(
    creator_id: Optional[int] = Query(None, description="创建者ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表"""
    # 权限检查
    if current_user.role == "developer":
        # 开发人员只能查看所有项目（用于选择）
        projects, total = ProjectService.get_projects(db, creator_id=None, skip=skip, limit=limit)
    elif current_user.role == "project_manager":
        # 项目经理可以查看所有项目，但默认只显示自己创建的
        if creator_id is None:
            creator_id = current_user.id
        projects, total = ProjectService.get_projects(db, creator_id=creator_id, skip=skip, limit=limit)
    else:
        # 开发组长和管理员可以查看所有项目
        projects, total = ProjectService.get_projects(db, creator_id=creator_id, skip=skip, limit=limit)
    
    # 填充创建者名称
    from app.models.user import User as UserModel
    for project in projects:
        if project.creator:
            project.creator_name = project.creator.full_name or project.creator.username
        else:
            # 如果relationship未加载，手动查询
            creator = db.query(UserModel).filter(UserModel.id == project.created_by).first()
            if creator:
                project.creator_name = creator.full_name or creator.username
    
    return ProjectListResponse(total=total, items=projects)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情"""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise NotFoundError("项目不存在")
    
    # 填充创建者名称
    from app.models.user import User as UserModel
    if project.creator:
        project.creator_name = project.creator.full_name or project.creator.username
    else:
        creator = db.query(UserModel).filter(UserModel.id == project.created_by).first()
        if creator:
            project.creator_name = creator.full_name or creator.username
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目"""
    try:
        project = ProjectService.update_project(db, project_id, project_data, current_user.id)
        return project
    except (NotFoundError, PermissionDeniedError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=str(e))
    except ValueError as e:
        raise ValidationError(str(e))


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目"""
    try:
        ProjectService.delete_project(db, project_id, current_user.id)
    except (NotFoundError, PermissionDeniedError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=str(e))


@router.get("/{project_id}/tasks", response_model=dict)
async def get_project_tasks(
    project_id: int,
    status: Optional[str] = Query(None, description="任务状态"),
    assignee_id: Optional[int] = Query(None, description="认领者ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目任务执行视图数据"""
    from app.models.task import Task, TaskStatus
    from app.models.task_schedule import TaskSchedule
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_
    
    # 检查项目是否存在
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise NotFoundError("项目不存在")
    
    # 权限检查：项目经理只能查看自己创建的项目
    if current_user.role == "project_manager" and project.created_by != current_user.id:
        raise PermissionDeniedError("只能查看自己创建的项目")
    
    # 构建查询
    query = db.query(Task).options(
        joinedload(Task.creator),
        joinedload(Task.assignee),
        joinedload(Task.project)
    ).filter(Task.project_id == project_id)
    
    # 状态筛选
    if status:
        query = query.filter(Task.status == status)
    
    # 认领者筛选
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    # 关键词搜索
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Task.title.like(keyword_pattern),
                Task.description.like(keyword_pattern)
            )
        )
    
    # 获取所有任务
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # 构建响应数据
    tasks_data = []
    for task in tasks:
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "creator_id": task.creator_id,
            "creator_name": task.creator.full_name or task.creator.username if task.creator else None,
            "assignee_id": task.assignee_id,
            "assignee_name": task.assignee.full_name or task.assignee.username if task.assignee else None,
            "estimated_man_days": float(task.estimated_man_days) if task.estimated_man_days else 0,
            "actual_man_days": float(task.actual_man_days) if task.actual_man_days else None,
            "required_skills": task.required_skills,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "is_pinned": task.is_pinned,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }
        
        # 获取排期信息
        from app.services.schedule_service import ScheduleService
        schedule = db.query(TaskSchedule).filter(TaskSchedule.task_id == task.id).first()
        if schedule:
            work_days = 0
            if schedule.start_date and schedule.end_date:
                work_days = ScheduleService.get_workdays_count(schedule.start_date, schedule.end_date, db)
            task_data["schedule"] = {
                "start_date": schedule.start_date.isoformat() if schedule.start_date else None,
                "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
                "work_days": work_days,
                "is_pinned": schedule.is_pinned,
            }
        
        tasks_data.append(task_data)
    
    # 按状态分组统计
    status_summary = {}
    for task in tasks:
        status = task.status
        if status not in status_summary:
            status_summary[status] = 0
        status_summary[status] += 1
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "tasks": tasks_data,
        "status_summary": status_summary,
        "total": len(tasks_data)
    }


@router.get("/{project_id}/progress", response_model=dict)
async def get_project_progress(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目进展数据"""
    from app.models.task import Task, TaskStatus
    from app.models.project_output_value import ProjectOutputValue
    from sqlalchemy import func
    from datetime import date, timedelta
    from decimal import Decimal
    
    # 检查项目是否存在
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise NotFoundError("项目不存在")
    
    # 权限检查：项目经理只能查看自己创建的项目
    if current_user.role == "project_manager" and project.created_by != current_user.id:
        raise PermissionDeniedError("只能查看自己创建的项目")
    
    # 1. 任务完成情况统计
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    draft_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.DRAFT.value
    ).count()
    published_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.PUBLISHED.value
    ).count()
    claimed_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.CLAIMED.value
    ).count()
    in_progress_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.IN_PROGRESS.value
    ).count()
    submitted_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.SUBMITTED.value
    ).count()
    confirmed_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.CONFIRMED.value
    ).count()
    archived_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.ARCHIVED.value
    ).count()
    
    # 计算任务完成率
    task_completion_rate = Decimal("0")
    if total_tasks > 0:
        task_completion_rate = Decimal(str(confirmed_tasks)) / Decimal(str(total_tasks)) * Decimal("100")
    
    # 2. 项目时间进度
    # 获取项目最早和最晚的任务时间
    earliest_task = db.query(Task).filter(
        Task.project_id == project_id
    ).order_by(Task.created_at.asc()).first()
    
    latest_task = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == TaskStatus.CONFIRMED.value
    ).order_by(Task.updated_at.desc()).first()
    
    project_start_date = project.created_at.date() if project.created_at else None
    project_end_date = None
    if latest_task and latest_task.updated_at:
        project_end_date = latest_task.updated_at.date()
    
    # 计算项目持续时间（天数）
    project_duration_days = 0
    if project_start_date and project_end_date:
        project_duration_days = (project_end_date - project_start_date).days + 1
    
    # 3. 项目产值数据
    output_value = db.query(ProjectOutputValue).filter(
        ProjectOutputValue.project_id == project_id
    ).first()
    
    estimated_value = project.estimated_output_value or Decimal("0")
    task_output_value = output_value.task_output_value if output_value else Decimal("0")
    allocated_output_value = output_value.allocated_output_value if output_value else Decimal("0")
    
    # 产值完成率
    output_completion_rate = Decimal("0")
    if estimated_value > 0:
        output_completion_rate = allocated_output_value / estimated_value * Decimal("100")
    
    # 4. 工作量统计（总投入人天）
    total_estimated_man_days = db.query(func.sum(Task.estimated_man_days)).filter(
        Task.project_id == project_id
    ).scalar() or Decimal("0")
    
    total_actual_man_days = db.query(func.sum(Task.actual_man_days)).filter(
        Task.project_id == project_id,
        Task.actual_man_days.isnot(None)
    ).scalar() or Decimal("0")
    
    # 5. 按时间维度的任务完成情况（最近6个月）
    today = date.today()
    monthly_stats = []
    for i in range(5, -1, -1):  # 最近6个月
        # 计算月份，处理跨年情况
        target_month = today.month - i
        target_year = today.year
        
        # 如果月份小于1，需要向前推一年
        while target_month < 1:
            target_month += 12
            target_year -= 1
        
        month_start = date(target_year, target_month, 1)
        # 计算月份最后一天
        if target_month == 12:
            month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(target_year, target_month + 1, 1) - timedelta(days=1)
        
        month_confirmed = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == TaskStatus.CONFIRMED.value,
            func.date(Task.updated_at) >= month_start,
            func.date(Task.updated_at) <= month_end
        ).count()
        
        monthly_stats.append({
            "month": f"{month_start.year}-{month_start.month:02d}",
            "confirmed_tasks": month_confirmed,
        })
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "project_start_date": project_start_date.isoformat() if project_start_date else None,
        "project_end_date": project_end_date.isoformat() if project_end_date else None,
        "project_duration_days": project_duration_days,
        "task_statistics": {
            "total": total_tasks,
            "draft": draft_tasks,
            "published": published_tasks,
            "claimed": claimed_tasks,
            "in_progress": in_progress_tasks,
            "submitted": submitted_tasks,
            "confirmed": confirmed_tasks,
            "archived": archived_tasks,
            "completion_rate": float(task_completion_rate),
        },
        "workload_statistics": {
            "total_estimated_man_days": float(total_estimated_man_days),
            "total_actual_man_days": float(total_actual_man_days),
        },
        "output_statistics": {
            "estimated_value": float(estimated_value),
            "task_output_value": float(task_output_value),
            "allocated_output_value": float(allocated_output_value),
            "completion_rate": float(output_completion_rate),
            "is_over_budget": task_output_value > estimated_value if estimated_value > 0 else False,
        },
        "monthly_statistics": monthly_stats,
    }
