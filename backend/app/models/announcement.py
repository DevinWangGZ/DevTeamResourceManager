"""系统公告模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class AnnouncementPriority:
    """公告优先级常量"""
    NORMAL = "normal"       # 普通
    IMPORTANT = "important" # 重要
    URGENT = "urgent"       # 紧急


class Announcement(Base):
    """系统公告模型
    
    仅系统管理员可创建/编辑/删除，所有用户可见。
    """
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(
        String(20),
        nullable=False,
        default=AnnouncementPriority.NORMAL,
        index=True
    )  # normal / important / urgent
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<Announcement(id={self.id}, title={self.title!r}, priority={self.priority})>"
