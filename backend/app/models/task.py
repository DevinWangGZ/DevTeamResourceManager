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


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.DRAFT,
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
        cascade="all, delete-orphan"
    )
    related_messages = relationship("Message", back_populates="related_task")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status}, assignee_id={self.assignee_id})>"
