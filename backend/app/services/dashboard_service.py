"""仪表盘服务"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.task import Task, TaskStatus
from app.models.workload_statistic import WorkloadStatistic
from app.models.project import Project
from app.models.project_output_value import ProjectOutputValue
from app.models.user import User
from app.models.user_sequence import UserSequence
from app.schemas.dashboard import (
    TaskSummary,
    WorkloadSummary,
    TodoReminder,
    DeveloperDashboardResponse,
    ProjectTaskSummary,
    ProjectOutputSummary,
    ProjectManagerDashboardResponse,
    TeamMemberSummary,
    TeamDashboardResponse
)
from app.services.workload_statistic_service import WorkloadStatisticService


class DashboardService:
    """仪表盘服务类"""

    @staticmethod
    def get_developer_dashboard(db: Session, user_id: int) -> DeveloperDashboardResponse:
        """获取开发人员工作台数据"""
        # 1. 任务汇总
        total_tasks = db.query(Task).filter(Task.assignee_id == user_id).count()
        in_progress = db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status == TaskStatus.IN_PROGRESS.value
        ).count()
        submitted = db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status == TaskStatus.SUBMITTED.value
        ).count()
        confirmed = db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status == TaskStatus.CONFIRMED.value
        ).count()
        pending_eval = db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status == TaskStatus.PENDING_EVAL.value
        ).count()

        task_summary = TaskSummary(
            total=total_tasks,
            in_progress=in_progress,
            submitted=submitted,
            confirmed=confirmed,
            pending_eval=pending_eval
        )

        # 2. 工作量汇总（当前月份）
        today = date.today()
        period_start = date(today.year, today.month, 1)
        if today.month == 12:
            period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

        workload_summary_data = WorkloadStatisticService.get_user_summary(
            db, user_id, period_start=period_start, period_end=period_end
        )

        workload_summary = WorkloadSummary(
            total_man_days=workload_summary_data['total_man_days'],
            project_count=workload_summary_data['project_count'],
            period_start=period_start,
            period_end=period_end
        )

        # 3. 待办提醒
        todo_reminders: List[TodoReminder] = []
        
        # 待评估任务提醒
        if pending_eval > 0:
            todo_reminders.append(TodoReminder(
                type="pending_eval",
                title="待评估任务",
                count=pending_eval,
                link="/tasks?status=pending_eval"
            ))
        
        # 已提交任务提醒（等待确认）
        if submitted > 0:
            todo_reminders.append(TodoReminder(
                type="submitted",
                title="已提交任务（等待确认）",
                count=submitted,
                link="/tasks?status=submitted"
            ))

        # 4. 最近任务（最近5个任务）
        recent_tasks = db.query(Task).filter(
            Task.assignee_id == user_id
        ).order_by(Task.updated_at.desc()).limit(5).all()

        recent_tasks_data = []
        for task in recent_tasks:
            recent_tasks_data.append({
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "project_id": task.project_id,
                "estimated_man_days": float(task.estimated_man_days) if task.estimated_man_days else None,
                "actual_man_days": float(task.actual_man_days) if task.actual_man_days else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            })

        return DeveloperDashboardResponse(
            task_summary=task_summary,
            workload_summary=workload_summary,
            todo_reminders=todo_reminders,
            recent_tasks=recent_tasks_data
        )

    @staticmethod
    def get_project_manager_dashboard(db: Session, user_id: int) -> ProjectManagerDashboardResponse:
        """获取项目经理仪表盘数据"""
        # 1. 获取用户创建的项目
        projects = db.query(Project).filter(Project.created_by == user_id).all()

        project_summaries: List[ProjectTaskSummary] = []
        output_summaries: List[ProjectOutputSummary] = []
        pending_confirmation_count = 0

        for project in projects:
            # 项目任务汇总
            total_tasks = db.query(Task).filter(Task.project_id == project.id).count()
            completed_tasks = db.query(Task).filter(
                Task.project_id == project.id,
                Task.status == TaskStatus.CONFIRMED.value
            ).count()
            in_progress_tasks = db.query(Task).filter(
                Task.project_id == project.id,
                Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value])
            ).count()
            pending_confirmation = db.query(Task).filter(
                Task.project_id == project.id,
                Task.status == TaskStatus.SUBMITTED.value
            ).count()

            pending_confirmation_count += pending_confirmation

            project_summaries.append(ProjectTaskSummary(
                project_id=project.id,
                project_name=project.name,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                in_progress_tasks=in_progress_tasks,
                pending_confirmation=pending_confirmation
            ))

            # 项目产值汇总
            output_value = db.query(ProjectOutputValue).filter(
                ProjectOutputValue.project_id == project.id
            ).first()

            if output_value:
                is_over_budget = output_value.task_output_value > project.estimated_output_value
                output_summaries.append(ProjectOutputSummary(
                    project_id=project.id,
                    project_name=project.name,
                    estimated_value=project.estimated_output_value,
                    task_output_value=output_value.task_output_value,
                    allocated_output_value=output_value.allocated_output_value,
                    is_over_budget=is_over_budget
                ))
            else:
                # 如果没有产值记录，创建默认值
                output_summaries.append(ProjectOutputSummary(
                    project_id=project.id,
                    project_name=project.name,
                    estimated_value=project.estimated_output_value or Decimal("0"),
                    task_output_value=Decimal("0"),
                    allocated_output_value=Decimal("0"),
                    is_over_budget=False
                ))

        # 2. 待办提醒
        todo_reminders: List[TodoReminder] = []
        
        if pending_confirmation_count > 0:
            todo_reminders.append(TodoReminder(
                type="pending_confirmation",
                title="待确认任务",
                count=pending_confirmation_count,
                link="/tasks?status=submitted"
            ))

        # 检查是否有超出预算的项目
        over_budget_projects = [s for s in output_summaries if s.is_over_budget]
        if over_budget_projects:
            todo_reminders.append(TodoReminder(
                type="over_budget",
                title="项目产值超出预算",
                count=len(over_budget_projects),
                link="/projects"
            ))

        return ProjectManagerDashboardResponse(
            project_summaries=project_summaries,
            output_summaries=output_summaries,
            pending_confirmation_count=pending_confirmation_count,
            todo_reminders=todo_reminders
        )

    @staticmethod
    def get_team_dashboard(db: Session) -> TeamDashboardResponse:
        """获取开发组长团队仪表盘数据"""
        # 1. 获取所有开发人员
        developers = db.query(User).filter(User.role == "developer", User.is_active == True).all()

        total_members = len(developers)
        member_summaries: List[TeamMemberSummary] = []

        # 计算总工作量和完成率
        total_workload = Decimal("0")
        total_tasks = 0
        completed_tasks = 0

        for developer in developers:
            # 获取开发人员的任务统计
            active_tasks = db.query(Task).filter(
                Task.assignee_id == developer.id,
                Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value])
            ).count()

            # 获取工作量统计（当前月份）
            today = date.today()
            period_start = date(today.year, today.month, 1)
            if today.month == 12:
                period_end = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

            workload_data = WorkloadStatisticService.get_user_summary(
                db, developer.id, period_start=period_start, period_end=period_end
            )

            total_man_days = workload_data['total_man_days']
            total_workload += total_man_days

            # 计算负荷状态（简化版：基于活跃任务数）
            if active_tasks >= 5:
                workload_status = "overloaded"
            elif active_tasks >= 2:
                workload_status = "normal"
            else:
                workload_status = "idle"

            member_summaries.append(TeamMemberSummary(
                user_id=developer.id,
                username=developer.username,
                full_name=developer.full_name,
                workload_status=workload_status,
                total_man_days=total_man_days,
                active_tasks=active_tasks
            ))

            # 统计任务完成情况
            user_total = db.query(Task).filter(Task.assignee_id == developer.id).count()
            user_completed = db.query(Task).filter(
                Task.assignee_id == developer.id,
                Task.status == TaskStatus.CONFIRMED.value
            ).count()

            total_tasks += user_total
            completed_tasks += user_completed

        # 计算完成率
        task_completion_rate = Decimal("0")
        if total_tasks > 0:
            task_completion_rate = Decimal(str(completed_tasks)) / Decimal(str(total_tasks)) * Decimal("100")

        # 2. 待办提醒
        todo_reminders: List[TodoReminder] = []
        
        # 过载人员提醒
        overloaded_members = [m for m in member_summaries if m.workload_status == "overloaded"]
        if overloaded_members:
            todo_reminders.append(TodoReminder(
                type="overloaded_members",
                title="过载人员提醒",
                count=len(overloaded_members),
                link="/team/workload"
            ))

        return TeamDashboardResponse(
            total_members=total_members,
            total_workload=total_workload,
            task_completion_rate=task_completion_rate,
            member_summaries=member_summaries,
            todo_reminders=todo_reminders
        )
