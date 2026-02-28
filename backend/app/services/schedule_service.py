"""任务排期服务

排期核心规则：
1. 串行队列：每人的任务按 优先级DESC + 认领时间ASC 排序串行执行
2. P0 任务认领后插队到串行队列最前（但不打断已进行中的任务）
3. 并发上限：每人同一时段内最多 3 个任务并发
4. 配合人排期与任务认领人排期保持一致（并发模式）
5. 排期自动跳过周末和法定节假日
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, case
from typing import Optional, List, Tuple
from datetime import date, timedelta
from decimal import Decimal

from app.models.task import Task, TaskStatus, TaskPriority, PRIORITY_ORDER
from app.models.task_schedule import TaskSchedule
from app.models.task_collaborator import TaskCollaborator
from app.models.holiday import Holiday
from app.core.exceptions import NotFoundError, ValidationError

# 每人同一时段内最多并发任务数
MAX_CONCURRENT_TASKS = 3


class ScheduleService:
    """任务排期服务类"""

    # ------------------------------------------------------------------
    # 工作日工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def is_workday(check_date: date, db: Session) -> bool:
        """判断指定日期是否为工作日（非周末且非法定节假日）"""
        if check_date.weekday() >= 5:
            return False
        holiday = db.query(Holiday).filter(Holiday.date == check_date).first()
        return holiday is None

    @staticmethod
    def get_workdays_count(start_date: date, end_date: date, db: Session) -> int:
        """计算两个日期之间的工作日数量（含首尾）"""
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if ScheduleService.is_workday(current_date, db):
                count += 1
            current_date += timedelta(days=1)
        return count

    @staticmethod
    def _next_workday(from_date: date, db: Session) -> date:
        """从 from_date 开始（含），找到下一个工作日"""
        d = from_date
        while not ScheduleService.is_workday(d, db):
            d += timedelta(days=1)
        return d

    @staticmethod
    def _calc_end_date(start_date: date, man_days: Decimal, db: Session) -> date:
        """从 start_date 开始，计算经过 man_days 个工作日后的结束日期"""
        workdays_needed = max(1, int(man_days))
        end_date = start_date
        workdays_count = 0
        while workdays_count < workdays_needed:
            if ScheduleService.is_workday(end_date, db):
                workdays_count += 1
            if workdays_count < workdays_needed:
                end_date += timedelta(days=1)
        return end_date

    # ------------------------------------------------------------------
    # 并发数查询
    # ------------------------------------------------------------------

    @staticmethod
    def get_concurrent_count(
        user_id: int,
        start: date,
        end: date,
        db: Session,
        exclude_task_id: Optional[int] = None
    ) -> int:
        """
        查询指定用户在 [start, end] 时间段内的并发任务数。
        同时统计：
          - 该用户作为认领人的任务（task_schedules）
          - 该用户作为配合人的任务（task_collaborators.scheduled_start/end）
        """
        # 认领人维度：排期与 [start, end] 有重叠的任务
        assignee_query = (
            db.query(TaskSchedule)
            .join(Task, Task.id == TaskSchedule.task_id)
            .filter(
                Task.assignee_id == user_id,
                Task.status.in_([
                    TaskStatus.CLAIMED.value,
                    TaskStatus.IN_PROGRESS.value,
                ]),
                TaskSchedule.start_date <= end,
                TaskSchedule.end_date >= start,
            )
        )
        if exclude_task_id:
            assignee_query = assignee_query.filter(Task.id != exclude_task_id)
        assignee_count = assignee_query.count()

        # 配合人维度：配合人排期与 [start, end] 有重叠
        collab_query = (
            db.query(TaskCollaborator)
            .join(Task, Task.id == TaskCollaborator.task_id)
            .filter(
                TaskCollaborator.user_id == user_id,
                TaskCollaborator.scheduled_start.isnot(None),
                TaskCollaborator.scheduled_start <= end,
                TaskCollaborator.scheduled_end >= start,
                Task.status.in_([
                    TaskStatus.CLAIMED.value,
                    TaskStatus.IN_PROGRESS.value,
                ]),
            )
        )
        if exclude_task_id:
            collab_query = collab_query.filter(Task.id != exclude_task_id)
        collab_count = collab_query.count()

        return assignee_count + collab_count

    # ------------------------------------------------------------------
    # 串行排期计算（核心）
    # ------------------------------------------------------------------

    @staticmethod
    def _get_serial_queue(
        db: Session,
        assignee_id: int,
        exclude_task_id: Optional[int] = None
    ) -> List[Task]:
        """
        获取开发人员串行队列中的任务列表（排除并发任务）。
        排序规则：优先级 DESC，同优先级按认领时间 ASC。
        """
        priority_order = case(
            PRIORITY_ORDER,
            value=Task.priority,
            else_=2
        )
        query = (
            db.query(Task)
            .outerjoin(TaskSchedule, TaskSchedule.task_id == Task.id)
            .filter(
                Task.assignee_id == assignee_id,
                Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]),
                # 排除并发任务（并发任务不占用串行队列位置）
                or_(
                    TaskSchedule.is_concurrent.is_(None),
                    TaskSchedule.is_concurrent == False
                ),
            )
            .order_by(priority_order, Task.created_at.asc())
        )
        if exclude_task_id:
            query = query.filter(Task.id != exclude_task_id)
        return query.all()

    @staticmethod
    def _rebuild_serial_schedules(
        db: Session,
        assignee_id: int,
        start_from: Optional[date] = None
    ) -> None:
        """
        重建某开发人员串行队列中所有任务的排期。
        规则：
        - 若有进行中任务，不中断，从其结束日期之后继续排队
        - P0 任务排在进行中任务之后（不打断当前任务）
        - 其余按优先级+认领时间排序
        """
        today = date.today()
        start_date = start_from or today

        # 获取串行队列
        queue = ScheduleService._get_serial_queue(db, assignee_id)
        if not queue:
            return

        # 找到当前进行中的任务（最多1个），保留其排期不变
        in_progress_task = next(
            (t for t in queue if t.status == TaskStatus.IN_PROGRESS.value), None
        )

        if in_progress_task:
            in_progress_schedule = db.query(TaskSchedule).filter(
                TaskSchedule.task_id == in_progress_task.id
            ).first()
            if in_progress_schedule:
                # 进行中任务的排期不变，后续从其结束日期次日起排
                next_start = ScheduleService._next_workday(
                    in_progress_schedule.end_date + timedelta(days=1), db
                )
            else:
                # 进行中任务没有排期记录，从今天起
                next_start = ScheduleService._next_workday(today, db)
        else:
            next_start = ScheduleService._next_workday(start_date, db)

        # 按队列顺序逐一排期（跳过进行中任务）
        for task in queue:
            if task.status == TaskStatus.IN_PROGRESS.value:
                continue  # 进行中任务排期保持不变

            end_date = ScheduleService._calc_end_date(next_start, task.estimated_man_days, db)

            schedule = db.query(TaskSchedule).filter(TaskSchedule.task_id == task.id).first()
            if schedule:
                schedule.start_date = next_start
                schedule.end_date = end_date
            else:
                schedule = TaskSchedule(
                    task_id=task.id,
                    start_date=next_start,
                    end_date=end_date,
                    is_pinned=False,
                    is_concurrent=False,
                )
                db.add(schedule)

            next_start = ScheduleService._next_workday(end_date + timedelta(days=1), db)

        db.flush()

    @staticmethod
    def calculate_schedule(
        db: Session,
        task_id: int,
        estimated_man_days: Decimal,
        assignee_id: int,
        start_from: Optional[date] = None
    ) -> TaskSchedule:
        """
        计算任务排期（认领时调用）。
        新任务加入串行队列后，重建整个队列排期。
        返回当前任务的 TaskSchedule。
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 重建整个串行队列排期（包含新任务）
        ScheduleService._rebuild_serial_schedules(db, assignee_id, start_from)

        # 确保当前任务有排期记录（rebuild 中已创建，此处保险性查询）
        schedule = db.query(TaskSchedule).filter(TaskSchedule.task_id == task_id).first()
        if not schedule:
            # 若任务没有进入串行队列（如状态不符），手动创建一条
            start_date = ScheduleService._next_workday(start_from or date.today(), db)
            end_date = ScheduleService._calc_end_date(start_date, estimated_man_days, db)
            schedule = TaskSchedule(
                task_id=task_id,
                start_date=start_date,
                end_date=end_date,
                is_pinned=False,
                is_concurrent=False,
            )
            db.add(schedule)

        db.commit()
        db.refresh(schedule)
        return schedule

    # ------------------------------------------------------------------
    # 置顶（兼容旧逻辑，现在通过重建队列实现）
    # ------------------------------------------------------------------

    @staticmethod
    def get_schedule(db: Session, task_id: int) -> Optional[TaskSchedule]:
        """获取任务排期"""
        return db.query(TaskSchedule).filter(TaskSchedule.task_id == task_id).first()

    @staticmethod
    def pin_task_and_reschedule(
        db: Session,
        task_id: int,
        is_pinned: bool,
        current_user_id: int
    ) -> TaskSchedule:
        """置顶/取消置顶任务并重新排期"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundError("任务", str(task_id))

        if task.assignee_id != current_user_id:
            raise ValidationError("只有任务认领者可以置顶任务")

        if task.status not in [TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]:
            raise ValidationError("只有已认领或进行中状态的任务可以置顶")

        task.is_pinned = is_pinned

        # 置顶通过临时调整 priority 字段实现排序优先
        # 重建整个队列排期
        ScheduleService._rebuild_serial_schedules(db, task.assignee_id)

        # 更新排期的置顶状态标记
        schedule = db.query(TaskSchedule).filter(TaskSchedule.task_id == task_id).first()
        if schedule:
            schedule.is_pinned = is_pinned

        db.commit()
        if schedule:
            db.refresh(schedule)
        return schedule

    # ------------------------------------------------------------------
    # 用户排期重算（手动触发）
    # ------------------------------------------------------------------

    @staticmethod
    def recalculate_user_schedules(db: Session, user_id: int) -> int:
        """
        重新计算指定用户串行队列中所有任务的排期。
        适用场景：任务提前完成/提交后，后续任务应前移但系统未自动更新时手动触发。
        返回本次重算涉及的任务数量。
        """
        # 获取串行队列任务数（重算前统计）
        queue = ScheduleService._get_serial_queue(db, user_id)
        task_count = len(queue)

        if task_count == 0:
            return 0

        # 同时也需要同步所有并发任务的配合人排期
        concurrent_task_ids = (
            db.query(TaskSchedule.task_id)
            .join(Task, Task.id == TaskSchedule.task_id)
            .filter(
                Task.assignee_id == user_id,
                TaskSchedule.is_concurrent == True,
                Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]),
            )
            .all()
        )

        # 重建串行队列排期
        ScheduleService._rebuild_serial_schedules(db, user_id)

        # 同步所有配合人排期（串行 + 并发任务）
        all_task_ids = [t.id for t in queue] + [r[0] for r in concurrent_task_ids]
        for tid in set(all_task_ids):
            ScheduleService.sync_collaborator_schedules(db, tid)

        db.commit()
        return task_count

    # ------------------------------------------------------------------
    # 用户排期查询
    # ------------------------------------------------------------------

    @staticmethod
    def get_user_schedules(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TaskSchedule]:
        """获取用户作为认领人的任务排期列表"""
        query = db.query(TaskSchedule).join(Task, Task.id == TaskSchedule.task_id).filter(
            Task.assignee_id == user_id
        )
        if start_date:
            query = query.filter(TaskSchedule.end_date >= start_date)
        if end_date:
            query = query.filter(TaskSchedule.start_date <= end_date)
        return query.order_by(TaskSchedule.start_date.asc()).all()

    @staticmethod
    def get_user_full_schedule(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[dict]:
        """
        获取用户完整排期（含作为认领人的任务 + 作为配合人的任务）。
        返回格式化的字典列表，供前端日历视图使用。
        """
        result = []

        # 1. 认领人维度
        assignee_schedules = ScheduleService.get_user_schedules(db, user_id, start_date, end_date)
        for sched in assignee_schedules:
            task = sched.task
            if not task:
                continue
            result.append({
                "task_id": task.id,
                "task_title": task.title,
                "priority": task.priority,
                "scheduled_start": sched.start_date,
                "scheduled_end": sched.end_date,
                "status": task.status,
                "estimated_days": float(task.estimated_man_days),
                "is_concurrent": sched.is_concurrent,
                "concurrent_with": sched.concurrent_with,
                "role": "assignee",
                "is_pinned": sched.is_pinned,
            })

        # 2. 配合人维度
        collab_query = (
            db.query(TaskCollaborator)
            .join(Task, Task.id == TaskCollaborator.task_id)
            .filter(
                TaskCollaborator.user_id == user_id,
                TaskCollaborator.scheduled_start.isnot(None),
            )
        )
        if start_date:
            collab_query = collab_query.filter(TaskCollaborator.scheduled_end >= start_date)
        if end_date:
            collab_query = collab_query.filter(TaskCollaborator.scheduled_start <= end_date)

        for collab in collab_query.all():
            task = collab.task
            if not task:
                continue
            result.append({
                "task_id": task.id,
                "task_title": task.title,
                "priority": task.priority,
                "scheduled_start": collab.scheduled_start,
                "scheduled_end": collab.scheduled_end,
                "status": task.status,
                "estimated_days": float(collab.allocated_man_days),
                "is_concurrent": True,
                "concurrent_with": None,
                "role": "collaborator",
                "is_pinned": False,
            })

        result.sort(key=lambda x: x["scheduled_start"] or date.max)
        return result

    # ------------------------------------------------------------------
    # 配合人排期同步
    # ------------------------------------------------------------------

    @staticmethod
    def sync_collaborator_schedules(db: Session, task_id: int) -> None:
        """
        同步所有配合人的排期与任务认领人的排期保持一致。
        在认领人排期变更后调用。
        """
        task_schedule = db.query(TaskSchedule).filter(
            TaskSchedule.task_id == task_id
        ).first()
        if not task_schedule:
            return

        collaborators = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task_id
        ).all()
        for collab in collaborators:
            collab.scheduled_start = task_schedule.start_date
            collab.scheduled_end = task_schedule.end_date

        db.flush()

    # ------------------------------------------------------------------
    # 并发任务设置
    # ------------------------------------------------------------------

    @staticmethod
    def check_concurrent_feasibility(
        db: Session,
        task_id: int,
        concurrent_with_task_id: int,
    ) -> Tuple[bool, List[dict], List[dict]]:
        """
        预检：查询将 task_id 设为与 concurrent_with_task_id 并发后，
        是否有人员并发数超限。
        返回 (can_set, exceeded_users, affected_schedules)
        """
        # 获取基准任务的排期
        base_schedule = db.query(TaskSchedule).filter(
            TaskSchedule.task_id == concurrent_with_task_id
        ).first()
        if not base_schedule:
            raise ValidationError("基准任务尚无排期，无法设为并发")

        target_task = db.query(Task).filter(Task.id == task_id).first()
        if not target_task:
            raise NotFoundError("任务", str(task_id))

        new_start = base_schedule.start_date
        new_end = base_schedule.end_date

        # 收集所有受影响的人员（认领人 + 配合人）
        affected_users = []

        # 目标任务的认领人
        if target_task.assignee_id:
            affected_users.append({
                "user_id": target_task.assignee_id,
                "role": "assignee",
            })

        # 目标任务的配合人
        collabs = db.query(TaskCollaborator).filter(
            TaskCollaborator.task_id == task_id
        ).all()
        for c in collabs:
            affected_users.append({
                "user_id": c.user_id,
                "role": "collaborator",
            })

        exceeded_users = []
        for au in affected_users:
            count = ScheduleService.get_concurrent_count(
                user_id=au["user_id"],
                start=new_start,
                end=new_end,
                db=db,
                exclude_task_id=task_id,
            )
            if count >= MAX_CONCURRENT_TASKS:
                from app.models.user import User
                user = db.query(User).filter(User.id == au["user_id"]).first()
                exceeded_users.append({
                    "user_id": au["user_id"],
                    "name": user.full_name or user.username if user else str(au["user_id"]),
                    "current_concurrent": count,
                    "limit": MAX_CONCURRENT_TASKS,
                })

        # 计算受影响的串行任务（会前移的任务）
        current_schedule = db.query(TaskSchedule).filter(
            TaskSchedule.task_id == task_id
        ).first()
        affected_serial = []
        if current_schedule and target_task.assignee_id:
            serial_queue = ScheduleService._get_serial_queue(
                db, target_task.assignee_id, exclude_task_id=task_id
            )
            # 当 task_id 从串行队列移走后，后续任务会整体前移
            # 找到 task_id 之后的任务，计算新排期
            found_current = False
            new_start_after = None
            for t in serial_queue:
                t_sched = db.query(TaskSchedule).filter(TaskSchedule.task_id == t.id).first()
                if t_sched and t_sched.start_date > (current_schedule.start_date or date.today()):
                    if not found_current:
                        found_current = True
                        # 空出来的位置由后续任务填充
                        new_start_after = current_schedule.start_date
                    if new_start_after and t_sched:
                        affected_serial.append({
                            "task_id": t.id,
                            "task_title": t.title,
                            "old_scheduled_start": t_sched.start_date,
                            "new_scheduled_start": new_start_after,
                        })
                        if new_start_after:
                            new_end_after = ScheduleService._calc_end_date(
                                new_start_after, t.estimated_man_days, db
                            )
                            new_start_after = ScheduleService._next_workday(
                                new_end_after + timedelta(days=1), db
                            )

        can_set = len(exceeded_users) == 0
        return can_set, exceeded_users, affected_serial

    @staticmethod
    def set_concurrent(
        db: Session,
        task_id: int,
        concurrent_with_task_id: int,
        current_user_id: int,
    ) -> TaskSchedule:
        """
        将 task_id 设为与 concurrent_with_task_id 并发执行。
        - 将 task_id 从串行队列移除
        - 其排期对齐到 concurrent_with_task_id 的排期
        - 校验所有相关人员并发数不超过 MAX_CONCURRENT_TASKS
        - 重建串行队列（后续任务前移）
        - 同步配合人排期
        """
        target_task = db.query(Task).filter(Task.id == task_id).first()
        if not target_task:
            raise NotFoundError("任务", str(task_id))

        if target_task.assignee_id != current_user_id:
            raise ValidationError("只有任务认领人可以设置并发")

        if target_task.status not in [TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]:
            raise ValidationError("只有已认领或进行中的任务可以设置并发")

        # 检查目标任务当前是否已经是并发任务
        target_schedule = db.query(TaskSchedule).filter(
            TaskSchedule.task_id == task_id
        ).first()
        if target_schedule and target_schedule.is_concurrent:
            raise ValidationError("该任务已经是并发任务，请先取消并发再重新设置")

        # 预检并发可行性（加行锁防止竞态）
        base_schedule = (
            db.query(TaskSchedule)
            .filter(TaskSchedule.task_id == concurrent_with_task_id)
            .with_for_update()
            .first()
        )
        if not base_schedule:
            raise ValidationError("基准任务尚无排期，无法设为并发")

        can_set, exceeded_users, _ = ScheduleService.check_concurrent_feasibility(
            db, task_id, concurrent_with_task_id
        )
        if not can_set:
            names = "、".join(u["name"] for u in exceeded_users)
            raise ValidationError(
                f"以下人员在任务重叠时间段内的并发任务数将超出上限（{MAX_CONCURRENT_TASKS}个）：{names}。"
                f"请与相关配合人确认排期，或变更配合人后再尝试设置并发。"
            )

        # 更新目标任务排期为并发模式
        new_start = base_schedule.start_date
        new_end = base_schedule.end_date

        if target_schedule:
            target_schedule.start_date = new_start
            target_schedule.end_date = new_end
            target_schedule.is_concurrent = True
            target_schedule.concurrent_with = concurrent_with_task_id
        else:
            target_schedule = TaskSchedule(
                task_id=task_id,
                start_date=new_start,
                end_date=new_end,
                is_pinned=False,
                is_concurrent=True,
                concurrent_with=concurrent_with_task_id,
            )
            db.add(target_schedule)

        db.flush()

        # 重建串行队列（task_id 已离开串行，后续任务前移）
        ScheduleService._rebuild_serial_schedules(db, target_task.assignee_id)

        # 同步配合人排期
        ScheduleService.sync_collaborator_schedules(db, task_id)

        db.commit()
        db.refresh(target_schedule)
        return target_schedule

    @staticmethod
    def unset_concurrent(
        db: Session,
        task_id: int,
        current_user_id: int,
    ) -> TaskSchedule:
        """
        取消任务的并发状态，将其重新归入串行队列并重算排期。
        """
        target_task = db.query(Task).filter(Task.id == task_id).first()
        if not target_task:
            raise NotFoundError("任务", str(task_id))

        if target_task.assignee_id != current_user_id:
            raise ValidationError("只有任务认领人可以取消并发")

        target_schedule = db.query(TaskSchedule).filter(
            TaskSchedule.task_id == task_id
        ).first()
        if not target_schedule or not target_schedule.is_concurrent:
            raise ValidationError("该任务当前不是并发任务")

        # 重置并发标记，让其重新进入串行队列
        target_schedule.is_concurrent = False
        target_schedule.concurrent_with = None
        db.flush()

        # 重建串行队列（task_id 重新加入）
        ScheduleService._rebuild_serial_schedules(db, target_task.assignee_id)

        # 同步配合人排期（排期可能已变更）
        ScheduleService.sync_collaborator_schedules(db, task_id)

        db.commit()
        db.refresh(target_schedule)
        return target_schedule
