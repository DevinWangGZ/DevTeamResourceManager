"""任务相关模式"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.task import TaskStatus


class TaskBase(BaseModel):
    """任务基础模式"""
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    project_id: Optional[int] = Field(None, description="项目ID")
    estimated_man_days: Decimal = Field(..., ge=0, description="拟投入人天")
    required_skills: Optional[str] = Field(None, description="所需技能（JSON格式或逗号分隔）")
    deadline: Optional[date] = Field(None, description="截止时间")


class TaskCreate(TaskBase):
    """创建任务请求"""
    pass


class TaskUpdate(BaseModel):
    """更新任务请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    project_id: Optional[int] = Field(None, description="项目ID")
    estimated_man_days: Optional[Decimal] = Field(None, ge=0, description="拟投入人天")
    required_skills: Optional[str] = Field(None, description="所需技能")
    deadline: Optional[date] = Field(None, description="截止时间")


class TaskPublish(BaseModel):
    """发布任务请求"""
    pass


class TaskClaim(BaseModel):
    """认领任务请求"""
    pass


class TaskAssign(BaseModel):
    """派发任务请求"""
    assignee_id: int = Field(..., description="被派发的开发人员ID")


class TaskEvaluate(BaseModel):
    """评估任务请求"""
    accept: bool = Field(..., description="是否接受任务")


class TaskSubmit(BaseModel):
    """提交任务请求"""
    actual_man_days: Decimal = Field(..., gt=0, description="实际投入人天")


class TaskConfirm(BaseModel):
    """确认任务请求"""
    pass


class TaskPin(BaseModel):
    """置顶任务请求"""
    is_pinned: bool = Field(..., description="是否置顶")


class TaskResponse(BaseModel):
    """任务响应"""
    id: int
    title: str
    description: Optional[str]
    status: str
    project_id: Optional[int]
    creator_id: int
    assignee_id: Optional[int]
    estimated_man_days: Decimal
    actual_man_days: Optional[Decimal]
    required_skills: Optional[str]
    deadline: Optional[date]
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    """任务详情响应（包含关联信息）"""
    creator_name: Optional[str] = None
    assignee_name: Optional[str] = None
    project_name: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    items: List[TaskResponse]


class TaskFilterParams(BaseModel):
    """任务筛选参数"""
    status: Optional[TaskStatus] = None
    project_id: Optional[int] = None
    creator_id: Optional[int] = None
    assignee_id: Optional[int] = None
    keyword: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
