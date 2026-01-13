"""项目模型"""
from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from app.models.base import Base


class Project(Base):
    """项目模型"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    estimated_output_value = Column(Numeric(15, 2))  # 预计产值（元）
    created_by = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    project_output_value = relationship(
        "ProjectOutputValue",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan"
    )
    workload_statistics = relationship("WorkloadStatistic", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, estimated_output_value={self.estimated_output_value})>"
