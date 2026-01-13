"""用户模型"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    DEVELOPER = "developer"
    PROJECT_MANAGER = "project_manager"
    DEVELOPMENT_LEAD = "development_lead"
    SYSTEM_ADMIN = "system_admin"


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(
        String(20),
        nullable=False,
        default=UserRole.DEVELOPER.value,
        index=True
    )
    status_tag = Column(String(50))  # 趣味化情绪标签，如 "🚀火力全开"
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    user_sequences = relationship("UserSequence", back_populates="user", cascade="all, delete-orphan")
    created_tasks = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    articles = relationship("Article", back_populates="author", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    workload_statistics = relationship("WorkloadStatistic", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
