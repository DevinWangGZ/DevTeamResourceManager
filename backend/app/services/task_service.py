"""任务服务"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Tuple
from datetime import date
from decimal import Decimal

from app.models.task import Task, TaskStatus, TaskPriority, PRIORITY_MULTIPLIER
from app.models.user import User
from app.models.project import Project
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilterParams
from app.services.schedule_service import ScheduleService
from app.services.workload_statistic_service import WorkloadStatisticService
from app.services.project_output_value_service import ProjectOutputValueService


class TaskService:
    """任务服务类"""

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate, creator_id: int) -> Task:
        """创建任务（草稿状态）"""
        priority = task_data.priority if task_data.priority else TaskPriority.P2.value
        multiplier = PRIORITY_MULTIPLIER.get(priority, Decimal("1.00"))
        task = Task(
            title=task_data.title,
            description=task_data.description,
            project_id=task_data.project_id,
            creator_id=creator_id,
            estimated_man_days=task_data.estimated_man_days,
            required_skills=task_data.required_skills,
            deadline=task_data.deadline,
            status=TaskStatus.DRAFT.value,
            priority=priority,
            priority_multiplier=multiplier,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """获取任务"""
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_tasks(
        db: Session,
        filters: TaskFilterParams,
        current_user_id: Optional[int] = None,
        current_user_role: Optional[str] = None,
        *,
        bypass_developer_visibility_for_single_project_export: bool = False,
    ) -> Tuple[List[Task], int]:
        """获取任务列表（支持筛选）"""
        from sqlalchemy.orm import joinedload
        
        query = db.query(Task).options(
            joinedload(Task.creator),
            joinedload(Task.assignee),
            joinedload(Task.project)
        )

        # 权限过滤：开发人员只能看到自己相关的任务或已发布的任务
        # 特例：按单项目导出已与 GET /projects/{id}/tasks 访问规则对齐时，不按该条收窄（导出与页面一致）
        if (
            current_user_role == "developer"
            and not bypass_developer_visibility_for_single_project_export
        ):
            query = query.filter(
                or_(
                    Task.status == TaskStatus.PUBLISHED.value,
                    Task.assignee_id == current_user_id,
                    Task.creator_id == current_user_id
                )
            )

        # 状态筛选（多选优先）
        if filters.statuses:
            query = query.filter(Task.status.in_([s.value for s in filters.statuses]))
        elif filters.status:
            query = query.filter(Task.status == filters.status.value)

        # 项目筛选（多选优先）
        if filters.project_ids:
            query = query.filter(Task.project_id.in_(filters.project_ids))
        elif filters.project_id:
            query = query.filter(Task.project_id == filters.project_id)

        # 创建者筛选（多选优先）
        if filters.creator_ids:
            query = query.filter(Task.creator_id.in_(filters.creator_ids))
        elif filters.creator_id:
            query = query.filter(Task.creator_id == filters.creator_id)

        # 认领者筛选（多选优先）
        if filters.assignee_ids:
            query = query.filter(Task.assignee_id.in_(filters.assignee_ids))
        elif filters.assignee_id:
            query = query.filter(Task.assignee_id == filters.assignee_id)

        # 关键词搜索（标题或描述）
        if filters.keyword:
            keyword = f"%{filters.keyword}%"
            query = query.filter(
                or_(
                    Task.title.like(keyword),
                    Task.description.like(keyword)
                )
            )

        # 技能筛选（所需技能包含指定技能）
        if filters.required_skills:
            skills_list = [s.strip() for s in filters.required_skills.split(',') if s.strip()]
            if skills_list:
                skill_filters = []
                for skill in skills_list:
                    skill_pattern = f"%{skill}%"
                    skill_filters.append(Task.required_skills.like(skill_pattern))
                if skill_filters:
                    query = query.filter(or_(*skill_filters))

        # 优先级筛选
        if filters.priority:
            query = query.filter(Task.priority == filters.priority)

        # 总数
        total = query.count()

        # 分页
        offset = (filters.page - 1) * filters.page_size
        tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(filters.page_size).all()

        return tasks, total

    @staticmethod
    def update_task(
        db: Session,
        task_id: int,
        task_data: TaskUpdate,
        current_user_id: int,
        current_user_role: str
    ) -> Task:
        """更新任务"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有创建者或管理员可以修改
        if task.creator_id != current_user_id and current_user_role != "system_admin":
            raise PermissionDeniedError("只有任务创建者或管理员可以修改任务")

        # 状态检查：已提交、已确认、已归档的任务不能修改
        if task.status in [TaskStatus.SUBMITTED.value, TaskStatus.CONFIRMED.value, TaskStatus.ARCHIVED.value]:
            raise ValidationError("已提交、已确认或已归档的任务不能修改")

        # 更新字段
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.project_id is not None:
            task.project_id = task_data.project_id
        if task_data.estimated_man_days is not None:
            task.estimated_man_days = task_data.estimated_man_days
        if task_data.required_skills is not None:
            task.required_skills = task_data.required_skills
        if task_data.deadline is not None:
            task.deadline = task_data.deadline
        if task_data.is_pinned is not None:
            task.is_pinned = task_data.is_pinned

        # 优先级只能在草稿或已发布状态修改（认领后锁定）
        if task_data.priority is not None:
            if task.status in [TaskStatus.DRAFT.value, TaskStatus.PUBLISHED.value]:
                task.priority = task_data.priority
                task.priority_multiplier = PRIORITY_MULTIPLIER.get(
                    task_data.priority, Decimal("1.00")
                )
            else:
                raise ValidationError("任务认领后优先级不可修改")

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def publish_task(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Task:
        """发布任务"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有创建者或项目经理可以发布
        if task.creator_id != current_user_id:
            if current_user_role not in ["project_manager", "system_admin"]:
                raise PermissionDeniedError("只有任务创建者或项目经理可以发布任务")

        # 状态检查：只有草稿状态可以发布
        if task.status != TaskStatus.DRAFT.value:
            raise ValidationError("只有草稿状态的任务可以发布")

        old_status = task.status
        task.status = TaskStatus.PUBLISHED.value
        db.commit()
        db.refresh(task)
        
        # 创建消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            # 消息创建失败不影响任务发布
            pass
        
        return task

    @staticmethod
    def revert_to_draft(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Task:
        """将已发布任务退回草稿"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有创建者或项目经理/管理员可以退回
        if task.creator_id != current_user_id:
            if current_user_role not in ["project_manager", "system_admin"]:
                raise PermissionDeniedError("只有任务创建者或项目经理可以退回任务")

        # 状态检查：只有已发布状态可以退回草稿
        if task.status != TaskStatus.PUBLISHED.value:
            raise ValidationError("只有已发布状态的任务可以退回草稿")

        old_status = task.status
        task.status = TaskStatus.DRAFT.value
        db.commit()
        db.refresh(task)

        # 创建消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            pass

        return task

    @staticmethod
    def return_task(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Task:
        """退回/收回已认领任务，状态回到"已发布"。
        
        - 认领人可主动退回（claimed / in_progress 状态均可）
        - 任务创建者或项目经理/管理员可强制收回
        退回后清除认领人、排期及配合人信息。
        """
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 状态检查
        allowed_statuses = [TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]
        if task.status not in allowed_statuses:
            raise ValidationError("只有已认领或进行中的任务可以退回/收回")

        # 权限检查：认领人可退回；创建者或 PM/管理员可收回
        is_assignee = task.assignee_id == current_user_id
        is_creator = task.creator_id == current_user_id
        is_manager = current_user_role in ["project_manager", "system_admin"]
        if not (is_assignee or is_creator or is_manager):
            raise PermissionDeniedError("只有任务认领人、创建者或项目经理可以退回/收回任务")

        old_assignee_id = task.assignee_id
        old_status = task.status

        # 清除认领信息，回到已发布
        task.status = TaskStatus.PUBLISHED.value
        task.assignee_id = None
        task.is_pinned = False

        # 删除排期（需要重新认领后重新生成）
        from app.models.task_schedule import TaskSchedule
        db.query(TaskSchedule).filter(TaskSchedule.task_id == task_id).delete()

        # 删除配合人记录
        from app.models.task_collaborator import TaskCollaborator
        db.query(TaskCollaborator).filter(TaskCollaborator.task_id == task_id).delete()

        db.commit()
        db.refresh(task)

        # 消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            pass

        return task

    @staticmethod
    def claim_task(
        db: Session,
        task_id: int,
        current_user_id: int
    ) -> Task:
        """认领任务（主动认领）"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 状态检查：只有已发布状态可以认领
        if task.status != TaskStatus.PUBLISHED.value:
            raise ValidationError("只有已发布状态的任务可以认领")

        # 检查是否已被认领
        if task.assignee_id is not None:
            raise ValidationError("任务已被认领")

        old_status = task.status
        task.status = TaskStatus.CLAIMED.value
        task.assignee_id = current_user_id
        db.commit()
        db.refresh(task)

        # 自动生成排期
        try:
            ScheduleService.calculate_schedule(
                db,
                task.id,
                task.estimated_man_days,
                current_user_id
            )
        except Exception as e:
            # 排期生成失败不影响任务认领
            pass

        # 创建消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            # 消息创建失败不影响任务认领
            pass

        return task

    @staticmethod
    def assign_task(
        db: Session,
        task_id: int,
        assignee_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Task:
        """派发任务给指定开发人员"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有项目经理可以派发任务
        if current_user_role not in ["project_manager", "system_admin"]:
            raise PermissionDeniedError("只有项目经理可以派发任务")

        # 状态检查：只有已发布状态可以派发
        if task.status != TaskStatus.PUBLISHED.value:
            raise ValidationError("只有已发布状态的任务可以派发")

        # 检查被派发用户是否存在且为开发人员
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise NotFoundError("用户", str(assignee_id))
        if assignee.role != "developer":
            raise ValidationError("只能派发给开发人员")

        old_status = task.status
        task.status = TaskStatus.PENDING_EVAL.value
        task.assignee_id = assignee_id
        db.commit()
        db.refresh(task)
        
        # 创建消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            # 消息创建失败不影响任务派发
            pass
        
        return task

    @staticmethod
    def evaluate_task(
        db: Session,
        task_id: int,
        accept: bool,
        current_user_id: int
    ) -> Task:
        """评估任务（接受或拒绝）"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 状态检查：只有待评估状态可以评估
        if task.status != TaskStatus.PENDING_EVAL.value:
            raise ValidationError("只有待评估状态的任务可以评估")

        # 权限检查：只有被派发的开发人员可以评估
        if task.assignee_id != current_user_id:
            raise PermissionDeniedError("只有被派发的开发人员可以评估任务")

        old_status = task.status
        if accept:
            # 接受：状态变为已认领
            task.status = TaskStatus.CLAIMED.value
            db.commit()
            db.refresh(task)

            # 自动生成排期
            try:
                ScheduleService.calculate_schedule(
                    db,
                    task.id,
                    task.estimated_man_days,
                    task.assignee_id
                )
            except Exception as e:
                # 排期生成失败不影响任务接受
                pass
            
            # 创建消息通知
            try:
                from app.services.message_service import MessageService
                MessageService.create_task_status_change_message(db, task, old_status, task.status)
            except Exception:
                # 消息创建失败不影响任务接受
                pass
        else:
            # 拒绝：状态变为已发布，清除认领者
            task.status = TaskStatus.PUBLISHED.value
            task.assignee_id = None
            db.commit()
            db.refresh(task)
            
            # 创建消息通知（通知项目经理任务被拒绝）
            try:
                from app.services.message_service import MessageService
                if task.creator_id:
                    MessageService.create_message(
                        db=db,
                        user_id=task.creator_id,
                        title="任务评估被拒绝",
                        content=f"任务《{task.title}》被开发人员拒绝，已重新发布。",
                        message_type="task_status_change",
                        related_task_id=task.id
                    )
            except Exception:
                # 消息创建失败不影响任务拒绝
                pass

        return task

    @staticmethod
    def start_task(
        db: Session,
        task_id: int,
        current_user_id: int
    ) -> Task:
        """开始任务（状态变为进行中）"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有认领者可以开始任务
        if task.assignee_id != current_user_id:
            raise PermissionDeniedError("只有任务认领者可以开始任务")

        # 状态检查：只有已认领状态可以开始
        if task.status != TaskStatus.CLAIMED.value:
            raise ValidationError("只有已认领状态的任务可以开始")

        old_status = task.status
        task.status = TaskStatus.IN_PROGRESS.value
        db.commit()
        db.refresh(task)
        
        # 创建消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            # 消息创建失败不影响任务开始
            pass
        
        return task

    @staticmethod
    def submit_task(
        db: Session,
        task_id: int,
        actual_man_days: Decimal,
        current_user_id: int
    ) -> Task:
        """提交任务"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有认领者可以提交任务
        if task.assignee_id != current_user_id:
            raise PermissionDeniedError("只有任务认领者可以提交任务")

        # 状态检查：只有已认领或进行中状态可以提交
        if task.status not in [TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]:
            raise ValidationError("只有已认领或进行中状态的任务可以提交")

        # 配合人分配合计：实际投入人天须不少于该合计
        from app.services.task_collaborator_service import TaskCollaboratorService
        collab_total = TaskCollaboratorService._calc_used_man_days(db, task_id)
        if collab_total > 0 and actual_man_days < collab_total:
            raise ValidationError(
                f"实际投入人天不能少于配合人分配合计。配合人分配合计：{collab_total} 人天，本次填写：{actual_man_days} 人天"
            )

        assignee_id = task.assignee_id
        old_status = task.status
        task.status = TaskStatus.SUBMITTED.value
        task.actual_man_days = actual_man_days
        db.commit()
        db.refresh(task)

        # 任务提交后，该任务退出串行队列，自动前移后续任务排期
        try:
            ScheduleService.recalculate_user_schedules(db, assignee_id)
        except Exception:
            pass

        # 创建消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            # 消息创建失败不影响任务提交
            pass
        
        return task

    @staticmethod
    def confirm_task(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role_codes: list
    ) -> Task:
        """确认任务。任务创建者、项目经理或系统管理员均可确认。"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：任务创建者、项目经理、系统管理员可以确认任务
        is_creator = task.creator_id == current_user_id
        is_manager = any(r in current_user_role_codes for r in ["project_manager", "system_admin"])
        if not (is_creator or is_manager):
            raise PermissionDeniedError("只有任务创建者、项目经理或系统管理员可以确认任务")

        # 状态检查：只有已提交状态可以确认
        if task.status != TaskStatus.SUBMITTED.value:
            raise ValidationError("只有已提交状态的任务可以确认")

        # 更新任务状态
        old_status = task.status
        task.status = TaskStatus.CONFIRMED.value
        db.commit()
        db.refresh(task)

        # 创建消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            # 消息创建失败不影响任务确认
            pass

        # 任务确认后，自动更新主认领人工作量统计
        try:
            WorkloadStatisticService.update_statistic_on_task_confirmation(db, task)
        except Exception as e:
            pass

        # 任务确认后，将配合人的分配人天汇入各自工作量统计
        try:
            from app.services.task_collaborator_service import TaskCollaboratorService
            TaskCollaboratorService.update_collaborators_workload_on_confirmation(db, task)
        except Exception:
            pass

        # 任务确认后，更新项目产值统计
        if task.project_id:
            try:
                ProjectOutputValueService.update_project_output_value(db, task.project_id)
            except Exception as e:
                pass

        return task

    @staticmethod
    def reject_task(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role_codes: list,
        reason: str
    ) -> Task:
        """退回已提交任务，状态回到"进行中"，并记录退回原因。
        任务创建者、项目经理、系统管理员可操作。
        """
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 状态检查：只有已提交状态可以退回
        if task.status != TaskStatus.SUBMITTED.value:
            raise ValidationError("只有已提交状态的任务可以退回")

        # 权限检查：任务创建者、项目经理、系统管理员可以退回
        is_creator = task.creator_id == current_user_id
        is_manager = any(r in current_user_role_codes for r in ["project_manager", "system_admin"])
        if not (is_creator or is_manager):
            raise PermissionDeniedError("只有任务创建者、项目经理或系统管理员可以退回任务")

        assignee_id = task.assignee_id
        old_status = task.status
        task.status = TaskStatus.IN_PROGRESS.value
        task.rejection_reason = reason

        db.commit()
        db.refresh(task)

        # 任务退回后重新进入串行队列，需重算排期（含后续任务）
        try:
            ScheduleService.recalculate_user_schedules(db, assignee_id)
        except Exception:
            pass

        # 消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            pass

        return task

    @staticmethod
    def reopen_task(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role_codes: list
    ) -> Task:
        """重新打开已确认任务，状态回到"进行中"。"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 状态检查：只有已确认状态可以重新打开
        if task.status != TaskStatus.CONFIRMED.value:
            raise ValidationError("只有已确认状态的任务可以重新打开")

        # 权限检查：任务创建者、项目经理、系统管理员可以重新打开
        is_creator = task.creator_id == current_user_id
        is_manager = any(r in current_user_role_codes for r in ["project_manager", "system_admin"])
        if not (is_creator or is_manager):
            raise PermissionDeniedError("只有任务创建者、项目经理或系统管理员可以重新打开任务")

        old_status = task.status
        task.status = TaskStatus.IN_PROGRESS.value

        # 先提交状态变更，再执行统计回滚
        db.commit()
        db.refresh(task)

        # 回滚主认领人的工作量统计（已确认时曾累加）
        try:
            if task.assignee_id and task.actual_man_days:
                WorkloadStatisticService.rollback_statistic_for_user(
                    db=db,
                    user_id=task.assignee_id,
                    project_id=task.project_id,
                    man_days=task.actual_man_days,
                    ref_date=task.updated_at.date() if task.updated_at else None,
                )
        except Exception:
            pass

        # 回滚配合人的工作量统计
        try:
            from app.services.task_collaborator_service import TaskCollaboratorService
            TaskCollaboratorService.rollback_collaborators_workload_on_reopen(db, task)
        except Exception:
            pass

        # 重新打开后，更新项目产值统计
        if task.project_id:
            try:
                ProjectOutputValueService.update_project_output_value(db, task.project_id)
            except Exception:
                pass

        # 消息通知
        try:
            from app.services.message_service import MessageService
            MessageService.create_task_status_change_message(db, task, old_status, task.status)
        except Exception:
            pass

        return task

    @staticmethod
    def pin_task(
        db: Session,
        task_id: int,
        is_pinned: bool,
        current_user_id: int
    ) -> Task:
        """置顶/取消置顶任务"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有认领者可以置顶任务
        if task.assignee_id != current_user_id:
            raise PermissionDeniedError("只有任务认领者可以置顶任务")

        # 状态检查：只有已认领或进行中状态可以置顶
        if task.status not in [TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]:
            raise ValidationError("只有已认领或进行中状态的任务可以置顶")

        # 使用排期服务处理置顶和重新排期
        schedule = ScheduleService.pin_task_and_reschedule(
            db,
            task_id,
            is_pinned,
            current_user_id
        )

        db.refresh(task)
        return task

    @staticmethod
    def delete_task(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> bool:
        """删除任务"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有创建者或管理员可以删除
        if task.creator_id != current_user_id and current_user_role != "system_admin":
            raise PermissionDeniedError("只有任务创建者或管理员可以删除任务")

        # 状态检查：只有草稿状态可以删除
        if task.status != TaskStatus.DRAFT.value:
            raise ValidationError("只有草稿状态的任务可以删除")

        db.delete(task)
        db.commit()
        return True
