"""工作量统计相关模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class WorkloadStatisticBase(BaseModel):
    """工作量统计基础模式"""
    user_id: int
    project_id: Optional[int] = None
    total_man_days: Decimal = Field(..., ge=0, description="总投入人天")
    period_start: date = Field(..., description="统计周期开始日期")
    period_end: date = Field(..., description="统计周期结束日期")


class WorkloadStatisticResponse(BaseModel):
    """工作量统计响应"""
    id: int
    user_id: int
    project_id: Optional[int]
    project_name: Optional[str] = None
    total_man_days: Decimal
    period_start: date
    period_end: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkloadStatisticListResponse(BaseModel):
    """工作量统计列表响应"""
    total: int
    items: list[WorkloadStatisticResponse]


class WorkloadStatisticFilterParams(BaseModel):
    """工作量统计筛选参数"""
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class WorkloadSummaryResponse(BaseModel):
    """工作量汇总响应"""
    user_id: int
    user_name: str
    total_man_days: Decimal
    project_count: int
    period_start: date
    period_end: date
