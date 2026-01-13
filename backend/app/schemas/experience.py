"""业务履历相关模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ExperienceBase(BaseModel):
    """业务履历基础模式"""
    project: str = Field(..., min_length=1, max_length=100, description="项目名称")
    module: Optional[str] = Field(None, max_length=100, description="模块名称")
    role: Optional[str] = Field(None, max_length=50, description="角色")
    description: Optional[str] = Field(None, description="贡献描述")
    man_days: Decimal = Field(..., ge=0, description="投入人天，支持小数（如0.5天）")


class ExperienceCreate(ExperienceBase):
    """创建业务履历请求"""
    pass


class ExperienceUpdate(BaseModel):
    """更新业务履历请求"""
    project: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    module: Optional[str] = Field(None, max_length=100, description="模块名称")
    role: Optional[str] = Field(None, max_length=50, description="角色")
    description: Optional[str] = Field(None, description="贡献描述")
    man_days: Optional[Decimal] = Field(None, ge=0, description="投入人天")


class ExperienceResponse(BaseModel):
    """业务履历响应"""
    id: int
    user_id: int
    project: str
    module: Optional[str]
    role: Optional[str]
    description: Optional[str]
    man_days: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExperienceListResponse(BaseModel):
    """业务履历列表响应"""
    total: int
    items: list[ExperienceResponse]
