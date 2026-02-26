"""系统公告 Pydantic 模式"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AnnouncementCreate(BaseModel):
    """创建公告请求"""
    title: str = Field(..., min_length=1, max_length=200, description="公告标题")
    content: str = Field(..., min_length=1, description="公告内容")
    priority: str = Field("normal", description="优先级: normal / important / urgent")
    is_active: bool = Field(True, description="是否启用")


class AnnouncementUpdate(BaseModel):
    """更新公告请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    priority: Optional[str] = None
    is_active: Optional[bool] = None


class AnnouncementResponse(BaseModel):
    """公告响应"""
    id: int
    title: str
    content: str
    priority: str
    is_active: bool
    author_id: int
    author_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnouncementListResponse(BaseModel):
    """公告列表响应"""
    total: int
    items: List[AnnouncementResponse]
