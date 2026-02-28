"""任务管理API端点"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

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
    SetConcurrentRequest,
    ConcurrentCheckResponse,
    ExceededUser,
    AffectedSchedule,
    UserScheduleResponse,
    UserScheduleItem,
    ProjectScheduleResponse,
    ProjectScheduleItem,
)
from app.schemas.task_comment import TaskCommentCreate, TaskCommentUpdate, TaskCommentResponse, TaskCommentListResponse
from app.services.task_service import TaskService
from app.services.task_collaborator_service import TaskCollaboratorService
from app.services.schedule_service import ScheduleService
from app.services.task_comment_service import TaskCommentService
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
    priority: Optional[str] = Query(None, description="优先级筛选：P0/P1/P2"),
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
        priority=priority,
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
    priority: Optional[str] = Query(None, description="优先级筛选：P0/P1/P2"),
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
        priority=priority,
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
            "priority": task.priority if hasattr(task, "priority") else "P2",
            "priority_multiplier": float(task.priority_multiplier) if hasattr(task, "priority_multiplier") and task.priority_multiplier else 1.0,
        }
        tasks_data.append(task_data)
    
    return {
        "tasks": tasks_data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============================================================
# 个人日程接口（固定路径，必须在 /{task_id} 路由之前注册）
# ============================================================

@router.get("/me/schedule", response_model=UserScheduleResponse)
async def get_my_schedule(
    start_date: Optional[date] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的完整排期（含认领任务和配合任务）"""
    schedule_list = ScheduleService.get_user_full_schedule(
        db, current_user.id, start_date, end_date
    )
    items = [UserScheduleItem(**item) for item in schedule_list]
    return UserScheduleResponse(schedule=items)


@router.post("/me/recalculate-schedule")
async def recalculate_my_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    手动触发当前用户的排期重算。
    适用于任务提前完成/提交后，后续任务排期未自动前移的情况。
    """
    task_count = ScheduleService.recalculate_user_schedules(db, current_user.id)
    return {"success": True, "message": f"排期重算完成，共更新 {task_count} 个任务的排期"}


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

    # 权限检查：管理员/项目经理/组长可查看所有任务；普通开发人员只能查看自己相关的任务
    # 兼容新字段 role_codes 和旧字段 role
    user_role_codes = [r.code for r in current_user.roles] if current_user.roles else []
    privileged_roles = {"project_manager", "development_lead", "system_admin"}
    has_privileged_role = (
        current_user.role in privileged_roles or
        bool(set(user_role_codes) & privileged_roles)
    )
    if not has_privileged_role:
        # 普通开发人员：只能查看已发布任务、自己认领/创建的任务，以及自己作为协助人的任务
        collaborator_ids = {c.user_id for c in task.collaborators} if task.collaborators else set()
        is_related = (
            task.status == TaskStatus.PUBLISHED.value or
            task.assignee_id == current_user.id or
            task.creator_id == current_user.id or
            current_user.id in collaborator_ids
        )
        if not is_related:
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


# ============================================================
# 并发排期接口
# ============================================================

@router.get("/{task_id}/concurrent-check", response_model=ConcurrentCheckResponse)
async def check_concurrent(
    task_id: int,
    concurrent_with_task_id: int = Query(..., description="基准任务ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """并发预检：查询设为并发后的可行性（不执行实际设置）"""
    from app.core.exceptions import NotFoundError, ValidationError as AppValidationError
    try:
        can_set, exceeded_users, affected_schedules = ScheduleService.check_concurrent_feasibility(
            db, task_id, concurrent_with_task_id
        )
    except (NotFoundError, AppValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ConcurrentCheckResponse(
        can_set_concurrent=can_set,
        exceeded_users=[ExceededUser(**u) for u in exceeded_users],
        affected_schedules=[AffectedSchedule(**s) for s in affected_schedules],
    )


@router.post("/{task_id}/set-concurrent", response_model=TaskScheduleResponse)
async def set_concurrent(
    task_id: int,
    data: SetConcurrentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将目标任务设置为与基准任务并发执行"""
    from app.core.exceptions import NotFoundError, ValidationError as AppValidationError
    try:
        schedule = ScheduleService.set_concurrent(
            db, task_id, data.concurrent_with_task_id, current_user.id
        )
    except AppValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    work_days = ScheduleService.get_workdays_count(schedule.start_date, schedule.end_date, db)
    return TaskScheduleResponse(
        id=schedule.id,
        task_id=schedule.task_id,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        is_pinned=schedule.is_pinned,
        work_days=work_days,
    )


@router.delete("/{task_id}/set-concurrent", response_model=TaskScheduleResponse)
async def unset_concurrent(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消任务的并发状态，重新归入串行队列"""
    from app.core.exceptions import NotFoundError, ValidationError as AppValidationError
    try:
        schedule = ScheduleService.unset_concurrent(db, task_id, current_user.id)
    except AppValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    work_days = ScheduleService.get_workdays_count(schedule.start_date, schedule.end_date, db)
    return TaskScheduleResponse(
        id=schedule.id,
        task_id=schedule.task_id,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        is_pinned=schedule.is_pinned,
        work_days=work_days,
    )


# ── 任务留言 ─────────────────────────────────────────────────────────────────

@router.get("/{task_id}/comments", response_model=TaskCommentListResponse)
async def get_task_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务留言列表（任务参与者可查看）"""
    from app.core.exceptions import NotFoundError, PermissionDeniedError
    try:
        comments = TaskCommentService.get_comments(db, task_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return TaskCommentListResponse(total=len(comments), items=comments)


@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=201)
async def create_task_comment(
    task_id: int,
    data: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发表任务留言（任务参与者可留言）"""
    from app.core.exceptions import NotFoundError, PermissionDeniedError
    try:
        return TaskCommentService.create_comment(db, task_id, current_user.id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/comments/{comment_id}", response_model=TaskCommentResponse)
async def update_task_comment(
    comment_id: int,
    data: TaskCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑留言（仅留言本人可操作）"""
    from app.core.exceptions import NotFoundError, PermissionDeniedError
    try:
        return TaskCommentService.update_comment(db, comment_id, current_user.id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_task_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除留言（仅留言本人可操作）"""
    from app.core.exceptions import NotFoundError, PermissionDeniedError
    try:
        TaskCommentService.delete_comment(db, comment_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


