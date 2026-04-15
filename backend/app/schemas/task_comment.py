"""任务留言相关模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCommentCreate(BaseModel):
    """创建留言请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="留言内容")


class TaskCommentUpdate(BaseModel):
    """更新留言请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="留言内容")


class TaskCommentResponse(BaseModel):
    """留言响应"""
    id: int
    task_id: int
    user_id: int
    user_name: str = Field(..., description="留言人姓名")
    user_full_name: Optional[str] = Field(None, description="留言人全名")
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCommentListResponse(BaseModel):
    """留言列表响应"""
    total: int
    items: list[TaskCommentResponse]
