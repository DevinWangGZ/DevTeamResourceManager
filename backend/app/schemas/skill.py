"""技能相关模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SkillBase(BaseModel):
    """技能基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="技能名称")
    proficiency: str = Field(..., description="熟练度: familiar(熟悉), proficient(熟练), expert(精通)")


class SkillCreate(SkillBase):
    """创建技能请求"""
    pass


class SkillUpdate(BaseModel):
    """更新技能请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="技能名称")
    proficiency: Optional[str] = Field(None, description="熟练度")


class SkillResponse(BaseModel):
    """技能响应"""
    id: int
    user_id: int
    name: str
    proficiency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """技能列表响应"""
    total: int
    items: list[SkillResponse]
