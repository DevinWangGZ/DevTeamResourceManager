"""任务管理API端点"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.core.permissions import get_current_project_manager
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskFilterParams,
    TaskPublish,
    TaskClaim,
    TaskAssign,
    TaskEvaluate,
    TaskSubmit,
    TaskConfirm,
    TaskReject,
    TaskPin,
    CollaboratorAdd,
    CollaboratorUpdate,
    CollaboratorResponse,
)
from app.services.task_service import TaskService
from app.services.task_collaborator_service import TaskCollaboratorService
from app.services.schedule_service import ScheduleService
from app.models.task import TaskStatus
from app.schemas.schedule import TaskScheduleResponse

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务（草稿状态）"""
    task = TaskService.create_task(db, task_data, current_user.id)
    return task


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    creator_id: Optional[int] = Query(None, description="创建者ID"),
    assignee_id: Optional[int] = Query(None, description="认领者ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    required_skills: Optional[str] = Query(None, description="所需技能（逗号分隔）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    filters = TaskFilterParams(
        status=status,
        project_id=project_id,
        creator_id=creator_id,
        assignee_id=assignee_id,
        keyword=keyword,
        required_skills=required_skills,
        page=page,
        page_size=page_size
    )
    tasks, total = TaskService.get_tasks(
        db,
        filters,
        current_user_id=current_user.id,
        current_user_role=current_user.role
    )
    return TaskListResponse(total=total, items=tasks)


@router.get("/marketplace", response_model=dict)
async def get_marketplace_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    required_skills: Optional[str] = Query(None, description="所需技能（逗号分隔）"),
    recommend: bool = Query(False, description="是否推荐（基于当前用户技能）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务集市数据（仅显示已发布的任务）"""
    from app.models.task import TaskStatus
    from app.models.skill import Skill
    
    # 只显示已发布的任务
    filters = TaskFilterParams(
        status=TaskStatus.PUBLISHED,
        project_id=project_id,
        keyword=keyword,
        required_skills=required_skills,
        page=page,
        page_size=page_size
    )
    
    tasks, total = TaskService.get_tasks(
        db,
        filters,
        current_user_id=current_user.id,
        current_user_role=current_user.role
    )
    
    # 如果启用推荐，基于用户技能进行排序
    if recommend and current_user.role == "developer":
        # 获取用户技能
        user_skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
        user_skill_names = {skill.name.lower() for skill in user_skills}
        
        # 计算每个任务的匹配度
        task_scores = []
        for task in tasks:
            score = 0
            if task.required_skills:
                task_skills = [s.strip().lower() for s in task.required_skills.split(',')]
                matched_skills = [s for s in task_skills if s in user_skill_names]
                if matched_skills:
                    score = len(matched_skills) / len(task_skills) if task_skills else 0
            
            task_scores.append((task, score))
        
        # 按匹配度排序（匹配度高的在前）
        task_scores.sort(key=lambda x: x[1], reverse=True)
        tasks = [task for task, _ in task_scores]
    
    # 构建响应数据
    tasks_data = []
    for task in tasks:
        task_data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "project_id": task.project_id,
            "project_name": task.project.name if task.project else None,
            "creator_id": task.creator_id,
            "creator_name": task.creator.full_name or task.creator.username if task.creator else None,
            "estimated_man_days": float(task.estimated_man_days) if task.estimated_man_days else 0,
            "required_skills": task.required_skills,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }
        tasks_data.append(task_data)
    
    return {
        "tasks": tasks_data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 权限检查：开发人员只能查看自己相关的任务或已发布的任务
    if current_user.role == "developer":
        if task.status != TaskStatus.PUBLISHED.value and \
           task.assignee_id != current_user.id and \
           task.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限查看此任务")

    # 构建响应
    response = TaskDetailResponse.model_validate(task)
    if task.creator:
        response.creator_name = task.creator.full_name or task.creator.username
    if task.assignee:
        response.assignee_name = task.assignee.full_name or task.assignee.username
    if task.project:
        response.project_name = task.project.name

    return response


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务"""
    task = TaskService.update_task(
        db,
        task_id,
        task_data,
        current_user.id,
        current_user.role
    )
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务（仅草稿状态）"""
    TaskService.delete_task(db, task_id, current_user.id, current_user.role)
    return None


@router.post("/{task_id}/publish", response_model=TaskResponse)
async def publish_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发布任务"""
    task = TaskService.publish_task(db, task_id, current_user.id, current_user.role)
    return task


@router.post("/{task_id}/return", response_model=TaskResponse)
async def return_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """退回/收回已认领任务到"已发布"状态。
    认领人可主动退回；任务创建者或项目经理/管理员可强制收回。
    """
    task = TaskService.return_task(db, task_id, current_user.id, current_user.role)
    return task


@router.post("/{task_id}/revert-draft", response_model=TaskResponse)
async def revert_task_to_draft(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """将已发布任务退回草稿"""
    task = TaskService.revert_to_draft(db, task_id, current_user.id, current_user.role)
    return task


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """认领任务（主动认领）"""
    # 只有开发人员可以认领任务
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="只有开发人员可以认领任务")

    task = TaskService.claim_task(db, task_id, current_user.id)
    return task


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    assign_data: TaskAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_project_manager)
):
    """派发任务给指定开发人员"""
    task = TaskService.assign_task(
        db,
        task_id,
        assign_data.assignee_id,
        current_user.id,
        current_user.role
    )
    return task


@router.post("/{task_id}/evaluate", response_model=TaskResponse)
async def evaluate_task(
    task_id: int,
    evaluate_data: TaskEvaluate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """评估任务（接受或拒绝）"""
    # 只有开发人员可以评估任务
    if current_user.role != "developer":
        raise HTTPException(status_code=403, detail="只有开发人员可以评估任务")

    task = TaskService.evaluate_task(
        db,
        task_id,
        evaluate_data.accept,
        current_user.id
    )
    return task


@router.post("/{task_id}/start", response_model=TaskResponse)
async def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """开始任务（状态变为进行中）"""
    task = TaskService.start_task(db, task_id, current_user.id)
    return task


@router.post("/{task_id}/submit", response_model=TaskResponse)
async def submit_task(
    task_id: int,
    submit_data: TaskSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交任务"""
    task = TaskService.submit_task(
        db,
        task_id,
        submit_data.actual_man_days,
        current_user.id
    )
    return task


@router.post("/{task_id}/confirm", response_model=TaskResponse)
async def confirm_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认任务。任务创建者、项目经理或系统管理员均可确认。"""
    role_codes = [role.code for role in current_user.roles] if current_user.roles else []
    task = TaskService.confirm_task(
        db,
        task_id,
        current_user.id,
        role_codes
    )
    return task


@router.post("/{task_id}/reject", response_model=TaskResponse)
async def reject_task(
    task_id: int,
    reject_data: TaskReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """退回已提交任务到"进行中"状态，并记录退回原因。
    任务创建者、项目经理或系统管理员可操作。
    """
    role_codes = [role.code for role in current_user.roles] if current_user.roles else []
    task = TaskService.reject_task(
        db,
        task_id,
        current_user.id,
        role_codes,
        reject_data.reason
    )
    return task


@router.post("/{task_id}/pin", response_model=TaskResponse)
async def pin_task(
    task_id: int,
    pin_data: TaskPin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """置顶/取消置顶任务（会自动重新排期）"""
    task = TaskService.pin_task(
        db,
        task_id,
        pin_data.is_pinned,
        current_user.id
    )
    return task


# ============================================================
# 任务配合人接口
# ============================================================

@router.get("/{task_id}/collaborators", response_model=list[CollaboratorResponse])
async def list_collaborators(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务的配合人列表"""
    return TaskCollaboratorService.list_collaborators(db, task_id)


@router.post("/{task_id}/collaborators", response_model=CollaboratorResponse, status_code=201)
async def add_collaborator(
    task_id: int,
    data: CollaboratorAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加任务配合人（仅任务认领人可操作）"""
    return TaskCollaboratorService.add_collaborator(db, task_id, data, current_user.id)


@router.put("/{task_id}/collaborators/{collaborator_user_id}", response_model=CollaboratorResponse)
async def update_collaborator(
    task_id: int,
    collaborator_user_id: int,
    data: CollaboratorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新配合人的分配人天（仅任务认领人可操作）"""
    return TaskCollaboratorService.update_collaborator(
        db, task_id, collaborator_user_id, data, current_user.id
    )


@router.delete("/{task_id}/collaborators/{collaborator_user_id}", status_code=204)
async def remove_collaborator(
    task_id: int,
    collaborator_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """移除配合人（仅任务认领人可操作）"""
    TaskCollaboratorService.remove_collaborator(db, task_id, collaborator_user_id, current_user.id)
    return None


@router.get("/{task_id}/schedule", response_model=TaskScheduleResponse)
async def get_task_schedule(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务排期"""
    schedule = ScheduleService.get_schedule(db, task_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="任务排期不存在")

    # 计算工作日数量
    work_days = ScheduleService.get_workdays_count(
        schedule.start_date,
        schedule.end_date,
        db
    )

    response = TaskScheduleResponse(
        id=schedule.id,
        task_id=schedule.task_id,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        is_pinned=schedule.is_pinned,
        work_days=work_days
    )

    return response
