"""数据导出服务"""
import io
import re
from urllib.request import urlopen
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.units import pixels_to_EMU
from sqlalchemy.orm import Session

from app.services.task_service import TaskService
from app.schemas.task import TaskFilterParams
from app.models.task import TaskStatus
from app.models.workload_statistic import WorkloadStatistic
from app.models.user import User
from app.models.project import Project


_MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


class ExportService:
    """数据导出服务类"""

    @staticmethod
    def _description_for_excel(description: Optional[str]) -> tuple[str, list[str]]:
        """
        「问题内容」在库中多为 Markdown：图片为 ![](url) / ![alt](url)。
        这里会把图片 URL 提取出来，并将正文中的 Markdown 图片语法移除，
        图片本体在导出时尝试嵌入到“问题图片”列。
        """
        if not description:
            return "", []
        text = description.strip()
        if not text:
            return "", []
        image_urls = [url.strip() for url in _MARKDOWN_IMAGE.findall(text) if url.strip()]
        cleaned = _MARKDOWN_IMAGE.sub("", text)
        # 清理图片语法留下的空白行，提升可读性
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned).strip()
        return cleaned, image_urls

    @staticmethod
    def _fetch_image_bytes(url: str) -> Optional[io.BytesIO]:
        """下载图片并返回内存流；失败时返回 None，避免导出整体失败。"""
        try:
            with urlopen(url, timeout=8) as resp:
                data = resp.read()
            if not data:
                return None
            return io.BytesIO(data)
        except Exception:
            return None

    @staticmethod
    def _scale_image(img: XLImage, max_width: int = 220, max_height: int = 140) -> None:
        """按比例缩放图片，限制在单元格可视区域。"""
        width = float(img.width or 0)
        height = float(img.height or 0)
        if width <= 0 or height <= 0:
            return
        scale = min(max_width / width, max_height / height, 1.0)
        img.width = int(width * scale)
        img.height = int(height * scale)

    @staticmethod
    def _add_images_to_same_cell(
        ws,
        row_idx: int,
        col_idx: int,
        image_urls: list[str],
        image_stream_refs: list[io.BytesIO],
    ) -> None:
        """
        在同一单元格内纵向偏移叠放多张图片。
        - 每张图缩放后按固定间距向下偏移
        - 动态抬高行高，确保全部可见
        """
        if not image_urls:
            return

        y_offset_px = 2
        gap_px = 6
        max_width_px = 210
        max_height_px = 120
        inserted = 0

        for url in image_urls:
            image_buffer = ExportService._fetch_image_bytes(url)
            if not image_buffer:
                continue
            try:
                image_stream_refs.append(image_buffer)
                excel_image = XLImage(image_buffer)
                ExportService._scale_image(excel_image, max_width=max_width_px, max_height=max_height_px)
                marker = AnchorMarker(
                    col=col_idx - 1,
                    colOff=pixels_to_EMU(2),
                    row=row_idx - 1,
                    rowOff=pixels_to_EMU(y_offset_px),
                )
                excel_image.anchor = OneCellAnchor(
                    _from=marker,
                    ext=(pixels_to_EMU(int(excel_image.width)), pixels_to_EMU(int(excel_image.height))),
                )
                ws.add_image(excel_image)
                y_offset_px += int(excel_image.height) + gap_px
                inserted += 1
            except Exception:
                continue

        if inserted > 0:
            ws.row_dimensions[row_idx].height = max(
                ws.row_dimensions[row_idx].height or 15,
                y_offset_px * 0.75 + 6,
            )

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
        filters: TaskFilterParams,
        current_user_id: int,
        current_user_role: str,
    ) -> io.BytesIO:
        """导出任务数据到Excel（筛选条件与任务列表 API 一致，最多 10000 条）。"""
        dumped = filters.model_dump()
        dumped["page"] = 1
        dumped["page_size"] = 10000
        export_filters = TaskFilterParams.model_construct(**dumped)
        tasks, _ = TaskService.get_tasks(
            db,
            export_filters,
            current_user_id=current_user_id,
            current_user_role=current_user_role,
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "任务列表"

        # 表头（「问题内容」对应模型 description，与任务描述一致）
        headers = [
            "任务ID", "标题", "问题内容", "问题图片", "项目", "状态", "创建人", "负责人", "拟投入人天", "实际投入人天",
            "创建时间", "更新时间"
        ]
        ws.append(headers)
        ExportService._apply_header_style(ws, 1, len(headers))
        image_stream_refs: list[io.BytesIO] = []

        # 填充数据
        for row_idx, task in enumerate(tasks, start=2):
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

            desc, image_urls = ExportService._description_for_excel(task.description)
            image_note = f"{len(image_urls)}张" if image_urls else ""
            ws.append([
                task.id,
                task.title,
                desc,
                image_note,
                project.name if project else "未分配项目",
                status_text,
                creator.full_name or creator.username if creator else "未知",
                assignee.full_name or assignee.username if assignee else "未分配",
                float(task.estimated_man_days) if task.estimated_man_days else 0,
                float(task.actual_man_days) if task.actual_man_days else 0,
                task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else "",
                task.updated_at.strftime("%Y-%m-%d %H:%M:%S") if task.updated_at else ""
            ])

            # 默认允许正文换行显示
            ws.cell(row=row_idx, column=3).alignment = Alignment(wrap_text=True, vertical="top")

            # 同一任务支持多图：都嵌入同一单元格并纵向偏移
            ExportService._add_images_to_same_cell(
                ws=ws,
                row_idx=row_idx,
                col_idx=4,
                image_urls=image_urls,
                image_stream_refs=image_stream_refs,
            )

        # 调整列宽
        column_widths = [10, 28, 40, 18, 20, 12, 15, 15, 12, 12, 20, 20]
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
