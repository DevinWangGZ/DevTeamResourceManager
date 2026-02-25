"""任务配合人模型"""
from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from app.models.base import Base


class TaskCollaborator(Base):
    """任务配合人模型
    
    记录参与同一任务协作的开发人员及其分配的人天数。
    由任务认领人（主负责人）负责添加配合人并分配人天。
    任务确认后，配合人的分配人天自动汇入其工作量统计和业务履历。
    """
    __tablename__ = "task_collaborators"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    allocated_man_days = Column(Numeric(10, 2), nullable=False, default=Decimal("0"))  # 分配给该配合人的人天
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 同一任务中同一用户只能作为一次配合人
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_collaborator"),
    )

    # 关系
    task = relationship("Task", back_populates="collaborators")
    user = relationship("User", back_populates="collaborating_tasks")

    def __repr__(self):
        return f"<TaskCollaborator(task_id={self.task_id}, user_id={self.user_id}, allocated_man_days={self.allocated_man_days})>"
