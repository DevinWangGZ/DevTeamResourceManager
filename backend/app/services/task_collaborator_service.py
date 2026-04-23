"""任务配合人服务"""
from sqlalchemy.orm import Session, joinedload
from typing import List
from decimal import Decimal

from app.models.task_collaborator import TaskCollaborator
from app.models.task_schedule import TaskSchedule
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.schemas.task import CollaboratorAdd, CollaboratorUpdate, CollaboratorResponse


class TaskCollaboratorService:
    """任务配合人服务类"""

    @staticmethod
    def _get_task_or_raise(db: Session, task_id: int) -> Task:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundError("任务", str(task_id))
        return task

    @staticmethod
    def _check_assignee_permission(task: Task, current_user_id: int) -> None:
        """校验当前用户是否为任务认领人（主负责人）"""
        if task.assignee_id != current_user_id:
            raise PermissionDeniedError("只有任务认领人可以管理配合人")

    @staticmethod
    def _check_task_in_active_status(task: Task) -> None:
        """校验任务处于可添加配合人的状态（已认领或进行中）"""
        allowed = [TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]
        if task.status not in allowed:
            raise ValidationError("只有已认领或进行中的任务可以管理配合人")

    @staticmethod
    def _calc_used_man_days(db: Session, task_id: int, exclude_user_id: int = None) -> Decimal:
        """计算任务中已分配给配合人的人天合计（可排除某个用户，用于更新场景）"""
        query = db.query(TaskCollaborator).filter(TaskCollaborator.task_id == task_id)
        if exclude_user_id is not None:
            query = query.filter(TaskCollaborator.user_id != exclude_user_id)
        records = query.all()
        return sum((r.allocated_man_days for r in records), Decimal("0"))

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    @staticmethod
    def list_collaborators(db: Session, task_id: int) -> List[CollaboratorResponse]:
        """获取任务的所有配合人列表"""
        records = (
            db.query(TaskCollaborator)
            .options(joinedload(TaskCollaborator.user))
            .filter(TaskCollaborator.task_id == task_id)
            .all()
        )
        result = []
        for r in records:
            result.append(CollaboratorResponse(
                id=r.id,
                task_id=r.task_id,
                user_id=r.user_id,
                user_name=r.user.username if r.user else None,
                user_full_name=r.user.full_name if r.user else None,
                allocated_man_days=r.allocated_man_days,
                scheduled_start=r.scheduled_start,
                scheduled_end=r.scheduled_end,
                created_at=r.created_at,
            ))
        return result

    # ------------------------------------------------------------------
    # 添加配合人
    # ------------------------------------------------------------------

    @staticmethod
    def add_collaborator(
        db: Session,
        task_id: int,
        data: CollaboratorAdd,
        current_user_id: int,
    ) -> CollaboratorResponse:
        """添加配合人。分配人天可超过任务拟投入；提交任务时由认领人填写的实际人天须不少于各配合人分配合计。"""
        task = TaskCollaboratorService._get_task_or_raise(db, task_id)
        TaskCollaboratorService._check_assignee_permission(task, current_user_id)
        TaskCollaboratorService._check_task_in_active_status(task)

        # 不能把自己（认领人）加为配合人
        if data.user_id == current_user_id:
            raise ValidationError("认领人不能将自己添加为配合人")

        # 被添加的用户必须存在且为开发人员
        user = db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise NotFoundError("用户", str(data.user_id))
        if user.role != "developer":
            raise ValidationError("配合人必须是开发人员角色")

        # 同一用户不可重复添加
        existing = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task_id,
            TaskCollaborator.user_id == data.user_id,
        ).first()
        if existing:
            raise ValidationError("该用户已是此任务的配合人")

        # 获取任务排期，校验配合人并发数
        from app.services.schedule_service import ScheduleService, MAX_CONCURRENT_TASKS
        task_schedule = db.query(TaskSchedule).filter(
            TaskSchedule.task_id == task_id
        ).first()

        if task_schedule and task_schedule.start_date and task_schedule.end_date:
            concurrent_count = ScheduleService.get_concurrent_count(
                user_id=data.user_id,
                start=task_schedule.start_date,
                end=task_schedule.end_date,
                db=db,
            )
            if concurrent_count >= MAX_CONCURRENT_TASKS:
                collab_user = db.query(User).filter(User.id == data.user_id).first()
                name = collab_user.full_name or collab_user.username if collab_user else str(data.user_id)
                raise ValidationError(
                    f"{name} 在该任务时间段内并发任务数已达上限（{MAX_CONCURRENT_TASKS}个），"
                    f"无法作为配合人。请调整任务排期或选择其他配合人。"
                )

        record = TaskCollaborator(
            task_id=task_id,
            user_id=data.user_id,
            allocated_man_days=data.allocated_man_days,
            scheduled_start=task_schedule.start_date if task_schedule else None,
            scheduled_end=task_schedule.end_date if task_schedule else None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return CollaboratorResponse(
            id=record.id,
            task_id=record.task_id,
            user_id=record.user_id,
            user_name=user.username,
            user_full_name=user.full_name,
            allocated_man_days=record.allocated_man_days,
            scheduled_start=record.scheduled_start,
            scheduled_end=record.scheduled_end,
            created_at=record.created_at,
        )

    # ------------------------------------------------------------------
    # 更新配合人人天
    # ------------------------------------------------------------------

    @staticmethod
    def update_collaborator(
        db: Session,
        task_id: int,
        collaborator_user_id: int,
        data: CollaboratorUpdate,
        current_user_id: int,
    ) -> CollaboratorResponse:
        """更新配合人的分配人天"""
        task = TaskCollaboratorService._get_task_or_raise(db, task_id)
        TaskCollaboratorService._check_assignee_permission(task, current_user_id)
        TaskCollaboratorService._check_task_in_active_status(task)

        record = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task_id,
            TaskCollaborator.user_id == collaborator_user_id,
        ).first()
        if not record:
            raise NotFoundError("配合人记录", f"task={task_id}, user={collaborator_user_id}")

        record.allocated_man_days = data.allocated_man_days
        db.commit()
        db.refresh(record)

        user = record.user
        return CollaboratorResponse(
            id=record.id,
            task_id=record.task_id,
            user_id=record.user_id,
            user_name=user.username if user else None,
            user_full_name=user.full_name if user else None,
            allocated_man_days=record.allocated_man_days,
            scheduled_start=record.scheduled_start,
            scheduled_end=record.scheduled_end,
            created_at=record.created_at,
        )

    # ------------------------------------------------------------------
    # 移除配合人
    # ------------------------------------------------------------------

    @staticmethod
    def remove_collaborator(
        db: Session,
        task_id: int,
        collaborator_user_id: int,
        current_user_id: int,
    ) -> None:
        """移除配合人"""
        task = TaskCollaboratorService._get_task_or_raise(db, task_id)
        TaskCollaboratorService._check_assignee_permission(task, current_user_id)
        TaskCollaboratorService._check_task_in_active_status(task)

        record = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task_id,
            TaskCollaborator.user_id == collaborator_user_id,
        ).first()
        if not record:
            raise NotFoundError("配合人记录", f"task={task_id}, user={collaborator_user_id}")

        db.delete(record)
        db.commit()

    # ------------------------------------------------------------------
    # 任务确认时汇入工作量统计（由 TaskService.confirm_task 调用）
    # ------------------------------------------------------------------

    @staticmethod
    def update_collaborators_workload_on_confirmation(db: Session, task: Task) -> None:
        """
        任务确认后，将各配合人的分配人天汇入其工作量统计。
        复用 WorkloadStatisticService 的统计逻辑。
        """
        from app.services.workload_statistic_service import WorkloadStatisticService

        collaborators = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task.id
        ).all()

        for collab in collaborators:
            if collab.allocated_man_days and collab.allocated_man_days > 0:
                try:
                    WorkloadStatisticService.update_statistic_for_user(
                        db=db,
                        user_id=collab.user_id,
                        project_id=task.project_id,
                        man_days=collab.allocated_man_days,
                        ref_date=task.updated_at.date() if task.updated_at else None,
                    )
                except Exception:
                    # 配合人统计失败不影响任务确认主流程
                    pass

    @staticmethod
    def rollback_collaborators_workload_on_reopen(db: Session, task: Task) -> None:
        """
        任务从已确认重新打开时，回滚配合人工作量统计。
        """
        from app.services.workload_statistic_service import WorkloadStatisticService

        collaborators = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task.id
        ).all()

        for collab in collaborators:
            if collab.allocated_man_days and collab.allocated_man_days > 0:
                try:
                    WorkloadStatisticService.rollback_statistic_for_user(
                        db=db,
                        user_id=collab.user_id,
                        project_id=task.project_id,
                        man_days=collab.allocated_man_days,
                        ref_date=task.updated_at.date() if task.updated_at else None,
                    )
                except Exception:
                    # 回滚失败不影响任务主流程
                    pass
