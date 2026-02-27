"""用户模型"""
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class UserRole(str, enum.Enum):
    """用户角色枚举（保留用于向后兼容和类型定义）"""
    DEVELOPER = "developer"
    PROJECT_MANAGER = "project_manager"
    DEVELOPMENT_LEAD = "development_lead"
    SYSTEM_ADMIN = "system_admin"


# 用户角色关联表
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    # 保留role字段用于向后兼容，但不再使用，使用roles关系代替
    role = Column(
        String(20),
        nullable=True,
        index=True,
        comment="已废弃，使用roles关系代替"
    )
    status_tag = Column(String(50))  # 趣味化情绪标签，如 "🚀火力全开"
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    skills = relationship("Skill", back_populates="user", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    user_sequences = relationship("UserSequence", back_populates="user", cascade="all, delete-orphan")
    created_tasks = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    articles = relationship("Article", back_populates="author", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    workload_statistics = relationship("WorkloadStatistic", back_populates="user", cascade="all, delete-orphan")
    collaborating_tasks = relationship("TaskCollaborator", back_populates="user", cascade="all, delete-orphan")
    task_comments = relationship("TaskComment", back_populates="user", cascade="all, delete-orphan")

    def has_role(self, role_code: str) -> bool:
        """检查用户是否拥有指定角色"""
        return any(role.code == role_code for role in self.roles)

    def has_any_role(self, role_codes: list[str]) -> bool:
        """检查用户是否拥有任意一个角色"""
        user_role_codes = {role.code for role in self.roles}
        return bool(user_role_codes.intersection(set(role_codes)))

    def get_role_codes(self) -> list[str]:
        """获取用户的所有角色代码列表"""
        return [role.code for role in self.roles]

    def __repr__(self):
        role_codes = ", ".join(self.get_role_codes()) if self.roles else "无角色"
        return f"<User(id={self.id}, username={self.username}, roles=[{role_codes}])>"
