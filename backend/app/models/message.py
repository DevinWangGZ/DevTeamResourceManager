"""消息通知模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class MessageType(str, enum.Enum):
    """消息类型枚举"""
    TASK_STATUS_CHANGE = "task_status_change"  # 任务状态变更
    TODO_REMINDER = "todo_reminder"            # 待办提醒
    SYSTEM_NOTICE = "system_notice"            # 系统通知


class Message(Base):
    """消息通知模型"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    type = Column(String(50), nullable=False)  # 消息类型
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    related_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)

    # 关系
    user = relationship("User", back_populates="messages")
    related_task = relationship("Task", back_populates="related_messages")

    def __repr__(self):
        return f"<Message(id={self.id}, user_id={self.user_id}, title={self.title}, is_read={self.is_read})>"
