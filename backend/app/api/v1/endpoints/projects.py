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
        schedule = db.query(TaskSchedule).filter(TaskSchedule.task_id == task.id).first()
        if schedule:
            task_data["schedule"] = {
                "start_date": schedule.start_date.isoformat() if schedule.start_date else None,
                "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
                "work_days": schedule.work_days,
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
