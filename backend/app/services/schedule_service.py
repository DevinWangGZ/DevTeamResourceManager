"""任务排期服务"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from datetime import date, timedelta
from decimal import Decimal

from app.models.task import Task, TaskStatus
from app.models.task_schedule import TaskSchedule
from app.models.holiday import Holiday
from app.core.exceptions import NotFoundError, ValidationError


class ScheduleService:
    """任务排期服务类"""

    @staticmethod
    def is_workday(check_date: date, db: Session) -> bool:
        """判断指定日期是否为工作日"""
        # 检查是否为周末（周六=5, 周日=6）
        if check_date.weekday() >= 5:
            return False

        # 检查是否为法定节假日
        holiday = db.query(Holiday).filter(Holiday.date == check_date).first()
        if holiday:
            return False

        return True

    @staticmethod
    def get_workdays_count(start_date: date, end_date: date, db: Session) -> int:
        """计算两个日期之间的工作日数量（包含开始和结束日期）"""
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if ScheduleService.is_workday(current_date, db):
                count += 1
            current_date += timedelta(days=1)
        return count

    @staticmethod
    def calculate_schedule(
        db: Session,
        task_id: int,
        estimated_man_days: Decimal,
        assignee_id: int,
        start_from: Optional[date] = None
    ) -> TaskSchedule:
        """计算任务排期"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 获取该开发人员已认领的任务（按认领时间排序，排除当前任务）
        existing_tasks = db.query(Task).filter(
            and_(
                Task.assignee_id == assignee_id,
                Task.id != task_id,
                Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value])
            )
        ).order_by(Task.created_at.asc()).all()

        # 获取已置顶的任务
        pinned_tasks = db.query(Task).filter(
            and_(
                Task.assignee_id == assignee_id,
                Task.id != task_id,
                Task.is_pinned == True,
                Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value])
            )
        ).order_by(Task.created_at.asc()).all()

        # 计算开始日期
        if start_from:
            start_date = start_from
        else:
            # 如果没有指定开始日期，从今天开始
            start_date = date.today()

        # 如果有已置顶的任务，从最后一个置顶任务的结束日期之后开始
        if pinned_tasks:
            last_pinned_schedule = db.query(TaskSchedule).filter(
                TaskSchedule.task_id == pinned_tasks[-1].id
            ).first()
            if last_pinned_schedule:
                start_date = last_pinned_schedule.end_date + timedelta(days=1)

        # 计算结束日期（基于工作日）
        workdays_needed = int(estimated_man_days)
        if workdays_needed < 1:
            workdays_needed = 1

        end_date = start_date
        workdays_count = 0

        # 跳过非工作日，计算结束日期
        while workdays_count < workdays_needed:
            if ScheduleService.is_workday(end_date, db):
                workdays_count += 1
            if workdays_count < workdays_needed:
                end_date += timedelta(days=1)

        # 创建或更新排期
        schedule = db.query(TaskSchedule).filter(TaskSchedule.task_id == task_id).first()
        if schedule:
            schedule.start_date = start_date
            schedule.end_date = end_date
        else:
            schedule = TaskSchedule(
                task_id=task_id,
                start_date=start_date,
                end_date=end_date,
                is_pinned=False
            )
            db.add(schedule)

        db.commit()
        db.refresh(schedule)
        return schedule

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
        """置顶任务并重新排期"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundError("任务", str(task_id))

        # 权限检查：只有认领者可以置顶任务
        if task.assignee_id != current_user_id:
            raise ValidationError("只有任务认领者可以置顶任务")

        # 状态检查：只有已认领或进行中状态可以置顶
        if task.status not in [TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value]:
            raise ValidationError("只有已认领或进行中状态的任务可以置顶")

        # 更新任务置顶状态
        task.is_pinned = is_pinned

        # 获取该开发人员的所有任务（按认领时间排序）
        all_tasks = db.query(Task).filter(
            and_(
                Task.assignee_id == task.assignee_id,
                Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value])
            )
        ).order_by(Task.created_at.asc()).all()

        # 重新计算所有任务的排期
        start_date = date.today()
        for t in all_tasks:
            # 置顶的任务排在前面
            if t.is_pinned and t.id != task_id:
                schedule = ScheduleService.calculate_schedule(
                    db,
                    t.id,
                    t.estimated_man_days,
                    t.assignee_id,
                    start_from=start_date
                )
                start_date = schedule.end_date + timedelta(days=1)

        # 如果当前任务被置顶，排在所有已置顶任务之后
        if is_pinned:
            pinned_tasks = [t for t in all_tasks if t.is_pinned and t.id != task_id]
            if pinned_tasks:
                last_pinned_schedule = db.query(TaskSchedule).filter(
                    TaskSchedule.task_id == pinned_tasks[-1].id
                ).first()
                if last_pinned_schedule:
                    start_date = last_pinned_schedule.end_date + timedelta(days=1)
            schedule = ScheduleService.calculate_schedule(
                db,
                task_id,
                task.estimated_man_days,
                task.assignee_id,
                start_from=start_date
            )
            start_date = schedule.end_date + timedelta(days=1)
        else:
            # 取消置顶，重新计算排期
            schedule = ScheduleService.calculate_schedule(
                db,
                task_id,
                task.estimated_man_days,
                task.assignee_id,
                start_from=start_date
            )
            start_date = schedule.end_date + timedelta(days=1)

        # 重新计算后续任务的排期
        for t in all_tasks:
            if t.id != task_id and not (is_pinned and t.is_pinned):
                schedule = ScheduleService.calculate_schedule(
                    db,
                    t.id,
                    t.estimated_man_days,
                    t.assignee_id,
                    start_from=start_date
                )
                start_date = schedule.end_date + timedelta(days=1)

        # 更新排期的置顶状态
        schedule = db.query(TaskSchedule).filter(TaskSchedule.task_id == task_id).first()
        if schedule:
            schedule.is_pinned = is_pinned
            db.commit()
            db.refresh(schedule)

        return schedule

    @staticmethod
    def get_user_schedules(
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TaskSchedule]:
        """获取用户的任务排期列表"""
        query = db.query(TaskSchedule).join(Task).filter(
            Task.assignee_id == user_id
        )

        if start_date:
            query = query.filter(TaskSchedule.start_date >= start_date)
        if end_date:
            query = query.filter(TaskSchedule.end_date <= end_date)

        return query.order_by(TaskSchedule.start_date.asc()).all()
