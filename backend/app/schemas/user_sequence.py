"""用户序列相关模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class UserSequenceBase(BaseModel):
    """用户序列基础模式"""
    level: str = Field(..., min_length=1, max_length=50, description="序列等级，如：初级开发、中级开发、高级开发")
    unit_price: Decimal = Field(..., gt=0, description="单价（元/人天），用于产值计算")


class UserSequenceCreate(UserSequenceBase):
    """创建用户序列请求"""
    pass


class UserSequenceUpdate(BaseModel):
    """更新用户序列请求"""
    level: Optional[str] = Field(None, min_length=1, max_length=50, description="序列等级")
    unit_price: Optional[Decimal] = Field(None, gt=0, description="单价（元/人天）")


class UserSequenceResponse(BaseModel):
    """用户序列响应"""
    id: int
    user_id: int
    level: str
    unit_price: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserSequenceListResponse(BaseModel):
    """用户序列列表响应"""
    total: int
    items: list[UserSequenceResponse]
