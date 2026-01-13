"""角色模型"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class RoleType(str, enum.Enum):
    """角色类型枚举"""
    DEVELOPER = "developer"
    PROJECT_MANAGER = "project_manager"
    DEVELOPMENT_LEAD = "development_lead"
    SYSTEM_ADMIN = "system_admin"


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True, comment="角色名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="角色代码")
    description = Column(Text, comment="角色描述")
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    users = relationship("User", secondary="user_roles", back_populates="roles")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, code={self.code})>"
