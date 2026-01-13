"""工作量统计模型"""
from sqlalchemy import Column, Integer, Numeric, Date, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from app.models.base import Base


class WorkloadStatistic(Base):
    """工作量统计模型"""
    __tablename__ = "workload_statistics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), index=True)
    total_man_days = Column(Numeric(10, 2), nullable=False, default=Decimal("0"))  # 总投入人天
    period_start = Column(Date, nullable=False, index=True)  # 统计周期开始日期
    period_end = Column(Date, nullable=False, index=True)    # 统计周期结束日期
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="workload_statistics")
    project = relationship("Project", back_populates="workload_statistics")

    def __repr__(self):
        return f"<WorkloadStatistic(id={self.id}, user_id={self.user_id}, project_id={self.project_id}, total_man_days={self.total_man_days})>"
