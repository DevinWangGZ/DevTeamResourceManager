"""任务服务"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Tuple
from datetime import date
from decimal import Decimal

from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilterParams
from app.services.schedule_service import ScheduleService
from app.services.workload_statistic_service import WorkloadStatisticService


class TaskService:
    """任务服务类"""

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate, creator_id: int) -> Task:
        """创建任务（草稿状态）"""
        task = Task(
            title=task_data.title,
            description=task_data.description,
            project_id=task_data.project_id,
            creator_id=creator_id,
            estimated_man_days=task_data.estimated_man_days,
            required_skills=task_data.required_skills,
            deadline=task_data.deadline,
            status=TaskStatus.DRAFT.value
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
        current_user_role: Optional[str] = None
    ) -> Tuple[List[Task], int]:
        """获取任务列表（支持筛选）"""
        query = db.query(Task)

        # 权限过滤：开发人员只能看到自己相关的任务或已发布的任务
        if current_user_role == "developer":
            query = query.filter(
                or_(
                    Task.status == TaskStatus.PUBLISHED.value,
                    Task.assignee_id == current_user_id,
                    Task.creator_id == current_user_id
                )
            )

        # 状态筛选
        if filters.status:
            query = query.filter(Task.status == filters.status.value)

        # 项目筛选
        if filters.project_id:
            query = query.filter(Task.project_id == filters.project_id)

        # 创建者筛选
        if filters.creator_id:
            query = query.filter(Task.creator_id == filters.creator_id)

        # 认领者筛选
        if filters.assignee_id:
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

        task.status = TaskStatus.PUBLISHED.value
        db.commit()
        db.refresh(task)
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

        task.status = TaskStatus.PENDING_EVAL.value
        task.assignee_id = assignee_id
        db.commit()
        db.refresh(task)
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
        else:
            # 拒绝：状态变为已发布，清除认领者
            task.status = TaskStatus.PUBLISHED.value
            task.assignee_id = None
            db.commit()
            db.refresh(task)

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

        task.status = TaskStatus.IN_PROGRESS.value
        db.commit()
        db.refresh(task)
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

        task.status = TaskStatus.SUBMITTED.value
        task.actual_man_days = actual_man_days
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def confirm_task(
        db: Session,
        task_id: int,
        current_user_id: int,
        current_user_role: str
    ) -> Task:
        """确认任务（项目经理确认）"""
        task = TaskService.get_task(db, task_id)
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有项目经理可以确认任务
        if current_user_role not in ["project_manager", "system_admin"]:
            raise PermissionDeniedError("只有项目经理可以确认任务")

        # 状态检查：只有已提交状态可以确认
        if task.status != TaskStatus.SUBMITTED.value:
            raise ValidationError("只有已提交状态的任务可以确认")

        # 更新任务状态
        task.status = TaskStatus.CONFIRMED.value
        db.commit()
        db.refresh(task)

        # 任务确认后，自动更新工作量统计
        try:
            WorkloadStatisticService.update_statistic_on_task_confirmation(db, task)
        except Exception as e:
            # 如果更新统计失败，记录错误但不影响任务确认
            # 在实际生产环境中，应该记录日志
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
