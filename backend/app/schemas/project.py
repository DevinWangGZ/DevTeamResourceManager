"""项目相关模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ProjectBase(BaseModel):
    """项目基础模式"""
    name: str = Field(..., description="项目名称", max_length=100)
    description: Optional[str] = Field(None, description="项目描述")
    estimated_output_value: Optional[Decimal] = Field(None, description="预计产值（元）")


class ProjectCreate(ProjectBase):
    """创建项目模式"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目模式"""
    name: Optional[str] = Field(None, description="项目名称", max_length=100)
    description: Optional[str] = Field(None, description="项目描述")
    estimated_output_value: Optional[Decimal] = Field(None, description="预计产值（元）")


class ProjectResponse(ProjectBase):
    """项目响应模式"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None  # 创建者名称

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应模式"""
    total: int
    items: list[ProjectResponse]
