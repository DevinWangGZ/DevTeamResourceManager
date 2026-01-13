"""项目产值统计服务"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.models.project_output_value import ProjectOutputValue
from app.models.task import Task, TaskStatus
from app.models.user_sequence import UserSequence


class ProjectOutputValueService:
    """项目产值统计服务类"""

    @staticmethod
    def update_project_output_value(db: Session, project_id: int) -> ProjectOutputValue:
        """
        更新项目产值统计
        
        计算逻辑：
        - task_output_value: 所有任务（已完成+未完成）的产值 = Σ(任务的实际投入人天 × 开发人员的序列单价)
        - allocated_output_value: 已完成任务的产值 = Σ(已确认任务的实际投入人天 × 开发人员的序列单价)
        """
        if not project_id:
            return None

        # 获取项目所有任务
        tasks = db.query(Task).filter(Task.project_id == project_id).all()

        task_output_value = Decimal("0")  # 所有任务的产值
        allocated_output_value = Decimal("0")  # 已确认任务的产值

        for task in tasks:
            if not task.assignee_id:
                continue

            # 获取开发人员的序列单价
            user_sequence = db.query(UserSequence).filter(
                UserSequence.user_id == task.assignee_id
            ).first()

            if not user_sequence or not user_sequence.unit_price:
                # 如果没有序列信息，跳过该任务
                continue

            # 根据任务状态计算产值
            if task.status == TaskStatus.CONFIRMED.value:
                # 已确认任务：使用实际投入人天
                if task.actual_man_days:
                    task_value = task.actual_man_days * user_sequence.unit_price
                    task_output_value += task_value
                    allocated_output_value += task_value
            elif task.status == TaskStatus.SUBMITTED.value:
                # 已提交但未确认：使用实际投入人天（如果有），否则使用拟投入人天
                if task.actual_man_days:
                    task_value = task.actual_man_days * user_sequence.unit_price
                    task_output_value += task_value
                elif task.estimated_man_days:
                    task_value = task.estimated_man_days * user_sequence.unit_price
                    task_output_value += task_value
            else:
                # 其他未完成任务：使用拟投入人天
                if task.estimated_man_days:
                    task_value = task.estimated_man_days * user_sequence.unit_price
                    task_output_value += task_value

        # 查找或创建项目产值记录
        output_value = db.query(ProjectOutputValue).filter(
            ProjectOutputValue.project_id == project_id
        ).first()

        if output_value:
            output_value.task_output_value = task_output_value
            output_value.allocated_output_value = allocated_output_value
        else:
            output_value = ProjectOutputValue(
                project_id=project_id,
                task_output_value=task_output_value,
                allocated_output_value=allocated_output_value
            )
            db.add(output_value)

        db.commit()
        db.refresh(output_value)
        return output_value
