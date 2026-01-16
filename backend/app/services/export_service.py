"""数据导出服务"""
import io
from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.workload_statistic import WorkloadStatistic
from app.models.user import User
from app.models.project import Project


class ExportService:
    """数据导出服务类"""

    @staticmethod
    def _create_header_style():
        """创建表头样式"""
        return {
            'font': Font(bold=True, color="FFFFFF"),
            'fill': PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid"),
            'alignment': Alignment(horizontal="center", vertical="center"),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        }

    @staticmethod
    def _apply_header_style(ws, row, max_col):
        """应用表头样式"""
        header_style = ExportService._create_header_style()
        for col in range(1, max_col + 1):
            cell = ws.cell(row=row, column=col)
            for attr, value in header_style.items():
                setattr(cell, attr, value)

    @staticmethod
    def export_workload_statistics(
        db: Session,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> io.BytesIO:
        """导出工作量统计数据到Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = "工作量统计"

        # 表头
        headers = [
            "统计周期", "用户", "项目", "任务数", "投入人天", "完成率", "创建时间"
        ]
        ws.append(headers)
        ExportService._apply_header_style(ws, 1, len(headers))

        # 查询数据
        query = db.query(WorkloadStatistic)
        if user_id:
            query = query.filter(WorkloadStatistic.user_id == user_id)
        if project_id:
            query = query.filter(WorkloadStatistic.project_id == project_id)
        if period_start:
            query = query.filter(WorkloadStatistic.period_start >= period_start)
        if period_end:
            query = query.filter(WorkloadStatistic.period_end <= period_end)

        statistics = query.order_by(WorkloadStatistic.period_start.desc()).all()

        # 填充数据
        for stat in statistics:
            user = db.query(User).filter(User.id == stat.user_id).first()
            project = db.query(Project).filter(Project.id == stat.project_id).first() if stat.project_id else None

            completion_rate = "0%"
            if stat.total_tasks > 0:
                completion_rate = f"{(stat.completed_tasks / stat.total_tasks * 100):.1f}%"

            ws.append([
                f"{stat.period_start} 至 {stat.period_end}",
                user.full_name or user.username if user else "未知",
                project.name if project else "未分配项目",
                stat.total_tasks,
                float(stat.total_man_days),
                completion_rate,
                stat.created_at.strftime("%Y-%m-%d %H:%M:%S") if stat.created_at else ""
            ])

        # 调整列宽
        column_widths = [20, 15, 20, 10, 12, 10, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def export_tasks(
        db: Session,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        assignee_id: Optional[int] = None
    ) -> io.BytesIO:
        """导出任务数据到Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = "任务列表"

        # 表头
        headers = [
            "任务ID", "标题", "项目", "状态", "创建人", "负责人", "拟投入人天", "实际投入人天",
            "创建时间", "更新时间"
        ]
        ws.append(headers)
        ExportService._apply_header_style(ws, 1, len(headers))

        # 查询数据
        from sqlalchemy.orm import joinedload
        query = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.creator),
            joinedload(Task.assignee)
        )
        if status:
            query = query.filter(Task.status == status)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if creator_id:
            query = query.filter(Task.creator_id == creator_id)
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)

        tasks = query.order_by(Task.created_at.desc()).limit(10000).all()

        # 填充数据
        for task in tasks:
            # 使用已加载的关联对象
            creator = task.creator
            assignee = task.assignee
            project = task.project

            status_text = {
                TaskStatus.DRAFT.value: "草稿",
                TaskStatus.PUBLISHED.value: "已发布",
                TaskStatus.CLAIMED.value: "已认领",
                TaskStatus.PENDING_EVAL.value: "待评估",
                TaskStatus.IN_PROGRESS.value: "进行中",
                TaskStatus.SUBMITTED.value: "已提交",
                TaskStatus.CONFIRMED.value: "已确认",
                TaskStatus.ARCHIVED.value: "已归档",
            }.get(task.status, task.status)

            ws.append([
                task.id,
                task.title,
                project.name if project else "未分配项目",
                status_text,
                creator.full_name or creator.username if creator else "未知",
                assignee.full_name or assignee.username if assignee else "未分配",
                float(task.estimated_man_days) if task.estimated_man_days else 0,
                float(task.actual_man_days) if task.actual_man_days else 0,
                task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else "",
                task.updated_at.strftime("%Y-%m-%d %H:%M:%S") if task.updated_at else ""
            ])

        # 调整列宽
        column_widths = [10, 30, 20, 12, 15, 15, 12, 12, 20, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output

    @staticmethod
    def export_performance_data(
        db: Session,
        user_id: Optional[int] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> io.BytesIO:
        """导出绩效数据到Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = "绩效数据"

        # 表头
        headers = [
            "用户", "序列等级", "统计周期", "完成任务数", "总任务数", "完成率",
            "总投入人天", "平均投入人天/任务", "创建时间"
        ]
        ws.append(headers)
        ExportService._apply_header_style(ws, 1, len(headers))

        # 查询数据
        query = db.query(WorkloadStatistic)
        if user_id:
            query = query.filter(WorkloadStatistic.user_id == user_id)
        if period_start:
            query = query.filter(WorkloadStatistic.period_start >= period_start)
        if period_end:
            query = query.filter(WorkloadStatistic.period_end <= period_end)

        statistics = query.order_by(WorkloadStatistic.period_start.desc()).all()

        # 填充数据
        for stat in statistics:
            user = db.query(User).filter(User.id == stat.user_id).first()
            if not user:
                continue

            # 获取序列等级
            from app.models.user_sequence import UserSequence
            sequence = db.query(UserSequence).filter(
                UserSequence.user_id == user.id
            ).order_by(UserSequence.created_at.desc()).first()
            sequence_level = sequence.level if sequence else "未设置"

            completion_rate = "0%"
            if stat.total_tasks > 0:
                completion_rate = f"{(stat.completed_tasks / stat.total_tasks * 100):.1f}%"

            avg_man_days = "0"
            if stat.completed_tasks > 0:
                avg_man_days = f"{(float(stat.total_man_days) / stat.completed_tasks):.2f}"

            ws.append([
                user.full_name or user.username,
                sequence_level,
                f"{stat.period_start} 至 {stat.period_end}",
                stat.completed_tasks,
                stat.total_tasks,
                completion_rate,
                float(stat.total_man_days),
                avg_man_days,
                stat.created_at.strftime("%Y-%m-%d %H:%M:%S") if stat.created_at else ""
            ])

        # 调整列宽
        column_widths = [15, 12, 25, 12, 12, 10, 12, 18, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width

        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output
