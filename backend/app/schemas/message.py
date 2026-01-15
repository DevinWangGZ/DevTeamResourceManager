"""消息通知相关模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """创建消息请求"""
    user_id: int = Field(..., description="接收用户ID")
    title: str = Field(..., description="消息标题")
    content: Optional[str] = Field(None, description="消息内容")
    type: str = Field(..., description="消息类型")
    related_task_id: Optional[int] = Field(None, description="关联任务ID")


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    user_id: int
    title: str
    content: Optional[str]
    type: str
    is_read: bool
    related_task_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """消息列表响应"""
    total: int
    items: list[MessageResponse]


class MessageUnreadCountResponse(BaseModel):
    """未读消息数量响应"""
    unread_count: int
