"""任务排期模型"""
from sqlalchemy import Column, Integer, Date, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class TaskSchedule(Base):
    """任务排期模型"""
    __tablename__ = "task_schedules"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    start_date = Column(Date, nullable=False, index=True)  # 预计开始日期
    end_date = Column(Date, nullable=False, index=True)   # 预计结束日期
    is_pinned = Column(Boolean, nullable=False, default=False)  # 是否置顶
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    task = relationship("Task", back_populates="task_schedule")

    def __repr__(self):
        return f"<TaskSchedule(id={self.id}, task_id={self.task_id}, start_date={self.start_date}, end_date={self.end_date})>"
