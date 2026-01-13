"""工作量统计服务"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Tuple, Optional
from datetime import date, datetime
from decimal import Decimal

from app.models.workload_statistic import WorkloadStatistic
from app.models.task import Task, TaskStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.workload_statistic import WorkloadStatisticFilterParams


class WorkloadStatisticService:
    """工作量统计服务类"""

    @staticmethod
    def update_statistic_on_task_confirmation(
        db: Session,
        task: Task,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> WorkloadStatistic:
        """
        任务确认时更新工作量统计
        
        当任务被确认后，将其实际投入人天计入开发人员的工作量统计
        如果指定周期内已有统计记录，则累加；否则创建新记录
        """
        if not task.assignee_id:
            raise ValidationError("任务没有分配开发人员")
        
        if not task.actual_man_days:
            raise ValidationError("任务没有实际投入人天数据")

        # 如果没有指定周期，使用任务提交日期所在月份作为统计周期
        if not period_start or not period_end:
            # 使用任务更新时间（确认时间）所在月份
            task_date = task.updated_at.date() if task.updated_at else date.today()
            period_start = date(task_date.year, task_date.month, 1)
            # 计算月份最后一天
            if task_date.month == 12:
                period_end = date(task_date.year + 1, 1, 1) - date.resolution
            else:
                period_end = date(task_date.year, task_date.month + 1, 1) - date.resolution

        # 查找是否已有该周期和项目的统计记录
        existing_stat = db.query(WorkloadStatistic).filter(
            and_(
                WorkloadStatistic.user_id == task.assignee_id,
                WorkloadStatistic.project_id == task.project_id,
                WorkloadStatistic.period_start == period_start,
                WorkloadStatistic.period_end == period_end
            )
        ).first()

        if existing_stat:
            # 累加工作量
            existing_stat.total_man_days += task.actual_man_days
            db.commit()
            db.refresh(existing_stat)
            return existing_stat
        else:
            # 创建新统计记录
            new_stat = WorkloadStatistic(
                user_id=task.assignee_id,
                project_id=task.project_id,
                total_man_days=task.actual_man_days,
                period_start=period_start,
                period_end=period_end
            )
            db.add(new_stat)
            db.commit()
            db.refresh(new_stat)
            return new_stat

    @staticmethod
    def get_statistics(
        db: Session,
        filters: WorkloadStatisticFilterParams
    ) -> Tuple[List[WorkloadStatistic], int]:
        """获取工作量统计列表"""
        query = db.query(WorkloadStatistic)

        # 应用筛选条件
        if filters.user_id:
            query = query.filter(WorkloadStatistic.user_id == filters.user_id)
        
        if filters.project_id:
            query = query.filter(WorkloadStatistic.project_id == filters.project_id)
        
        if filters.period_start:
            query = query.filter(WorkloadStatistic.period_start >= filters.period_start)
        
        if filters.period_end:
            query = query.filter(WorkloadStatistic.period_end <= filters.period_end)

        # 获取总数
        total = query.count()

        # 分页和排序
        statistics = query.order_by(
            WorkloadStatistic.period_start.desc(),
            WorkloadStatistic.user_id.asc()
        ).offset(filters.skip).limit(filters.limit).all()

        return statistics, total

    @staticmethod
    def get_user_statistics(
        db: Session,
        user_id: int,
        project_id: Optional[int] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> List[WorkloadStatistic]:
        """获取指定用户的工作量统计"""
        query = db.query(WorkloadStatistic).filter(
            WorkloadStatistic.user_id == user_id
        )

        if project_id:
            query = query.filter(WorkloadStatistic.project_id == project_id)
        
        if period_start:
            query = query.filter(WorkloadStatistic.period_start >= period_start)
        
        if period_end:
            query = query.filter(WorkloadStatistic.period_end <= period_end)

        return query.order_by(
            WorkloadStatistic.period_start.desc(),
            WorkloadStatistic.project_id.asc()
        ).all()

    @staticmethod
    def get_project_statistics(
        db: Session,
        project_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> List[WorkloadStatistic]:
        """获取指定项目的工作量统计"""
        query = db.query(WorkloadStatistic).filter(
            WorkloadStatistic.project_id == project_id
        )

        if period_start:
            query = query.filter(WorkloadStatistic.period_start >= period_start)
        
        if period_end:
            query = query.filter(WorkloadStatistic.period_end <= period_end)

        return query.order_by(
            WorkloadStatistic.period_start.desc(),
            WorkloadStatistic.user_id.asc()
        ).all()

    @staticmethod
    def get_user_summary(
        db: Session,
        user_id: int,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> dict:
        """获取用户工作量汇总"""
        query = db.query(
            WorkloadStatistic.user_id,
            func.sum(WorkloadStatistic.total_man_days).label('total_man_days'),
            func.count(func.distinct(WorkloadStatistic.project_id)).label('project_count')
        ).filter(WorkloadStatistic.user_id == user_id)

        if period_start:
            query = query.filter(WorkloadStatistic.period_start >= period_start)
        
        if period_end:
            query = query.filter(WorkloadStatistic.period_end <= period_end)

        result = query.group_by(WorkloadStatistic.user_id).first()

        if result:
            return {
                'user_id': result.user_id,
                'total_man_days': result.total_man_days or Decimal('0'),
                'project_count': result.project_count or 0
            }
        else:
            return {
                'user_id': user_id,
                'total_man_days': Decimal('0'),
                'project_count': 0
            }
