"""项目产值统计模型"""
from sqlalchemy import Column, Integer, Numeric, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from app.models.base import Base


class ProjectOutputValue(Base):
    """项目产值统计模型"""
    __tablename__ = "project_output_values"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    task_output_value = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))  # 任务产值（已完成+未完成）
    allocated_output_value = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))  # 已分配产值（已完成任务）
    calculated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="project_output_value")

    def __repr__(self):
        return f"<ProjectOutputValue(id={self.id}, project_id={self.project_id}, task_output_value={self.task_output_value}, allocated_output_value={self.allocated_output_value})>"
