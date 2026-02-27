"""任务模型"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, Date, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
import enum

from app.models.base import Base


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    DRAFT = "draft"              # 草稿
    PUBLISHED = "published"     # 已发布
    PENDING_EVAL = "pending_eval"  # 待评估（派发任务时）
    CLAIMED = "claimed"         # 已认领
    IN_PROGRESS = "in_progress" # 进行中
    SUBMITTED = "submitted"     # 已提交
    CONFIRMED = "confirmed"     # 已确认
    ARCHIVED = "archived"       # 已归档


class TaskPriority(str, enum.Enum):
    """任务优先级枚举"""
    P0 = "P0"  # 最紧急，产值溢价 20%
    P1 = "P1"  # 较紧急，产值溢价 10%
    P2 = "P2"  # 常规，无溢价（默认）


# 优先级对应的溢价系数
PRIORITY_MULTIPLIER = {
    TaskPriority.P0.value: Decimal("1.20"),
    TaskPriority.P1.value: Decimal("1.10"),
    TaskPriority.P2.value: Decimal("1.00"),
}

# 优先级排序权重（数值越小优先级越高，用于 SQL ORDER BY）
PRIORITY_ORDER = {
    TaskPriority.P0.value: 0,
    TaskPriority.P1.value: 1,
    TaskPriority.P2.value: 2,
}


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(
        String(20),
        nullable=False,
        default=TaskStatus.DRAFT.value,
        index=True
    )
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), index=True)
    estimated_man_days = Column(Numeric(10, 2), nullable=False, default=Decimal("0"))  # 拟投入人天（PM填写）
    actual_man_days = Column(Numeric(10, 2))  # 实际投入人天（开发者填写）
    required_skills = Column(Text)  # 所需技能（JSON格式或逗号分隔）
    deadline = Column(Date)
    is_pinned = Column(Boolean, nullable=False, default=False)  # 是否置顶
    rejection_reason = Column(Text)  # 退回原因（发起人/PM 退回已提交任务时填写）
    # 优先级与溢价（P2 为默认，认领后不可更改）
    priority = Column(String(2), nullable=False, default=TaskPriority.P2.value, index=True)
    priority_multiplier = Column(Numeric(4, 2), nullable=False, default=Decimal("1.00"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    project = relationship("Project", back_populates="tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    task_schedule = relationship(
        "TaskSchedule",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="[TaskSchedule.task_id]",
    )
    related_messages = relationship("Message", back_populates="related_task")
    collaborators = relationship(
        "TaskCollaborator",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at.desc()"
    )

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status}, assignee_id={self.assignee_id})>"
