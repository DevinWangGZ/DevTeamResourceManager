"""任务相关模式"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """任务基础模式"""
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    project_id: Optional[int] = Field(None, description="项目ID")
    estimated_man_days: Decimal = Field(..., ge=0, description="拟投入人天")
    required_skills: Optional[str] = Field(None, description="所需技能（JSON格式或逗号分隔）")
    deadline: Optional[date] = Field(None, description="截止时间")
    priority: str = Field(TaskPriority.P2.value, description="优先级：P0/P1/P2，默认P2")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = [p.value for p in TaskPriority]
        if v not in allowed:
            raise ValueError(f"优先级必须为 {allowed} 之一")
        return v


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
    is_pinned: Optional[bool] = Field(None, description="是否置顶（用于优先级）")
    priority: Optional[str] = Field(None, description="优先级：P0/P1/P2（仅草稿/已发布状态可修改）")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = [p.value for p in TaskPriority]
        if v not in allowed:
            raise ValueError(f"优先级必须为 {allowed} 之一")
        return v


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


class TaskReject(BaseModel):
    """退回已提交任务请求"""
    reason: str = Field(..., min_length=1, max_length=500, description="退回原因")


class TaskPin(BaseModel):
    """置顶任务请求"""
    is_pinned: bool = Field(..., description="是否置顶")


class TaskScheduleInfo(BaseModel):
    """任务排期信息（嵌入 TaskResponse）"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_pinned: bool = False
    is_concurrent: bool = False
    concurrent_with: Optional[int] = None

    class Config:
        from_attributes = True


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
    rejection_reason: Optional[str] = None
    priority: str = TaskPriority.P2.value
    priority_multiplier: Decimal = Decimal("1.00")
    schedule: Optional[TaskScheduleInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    """任务详情响应（包含关联信息）"""
    creator_name: Optional[str] = None
    assignee_name: Optional[str] = None
    project_name: Optional[str] = None


class TaskListItemResponse(TaskResponse):
    """任务列表项响应（包含关联信息）"""
    creator_name: Optional[str] = None
    assignee_name: Optional[str] = None
    project_name: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    items: List[TaskListItemResponse]


class TaskFilterParams(BaseModel):
    """任务筛选参数"""
    status: Optional[TaskStatus] = None
    statuses: Optional[List[TaskStatus]] = None
    project_id: Optional[int] = None
    project_ids: Optional[List[int]] = None
    creator_id: Optional[int] = None
    creator_ids: Optional[List[int]] = None
    assignee_id: Optional[int] = None
    assignee_ids: Optional[List[int]] = None
    keyword: Optional[str] = None
    required_skills: Optional[str] = None  # 所需技能（逗号分隔）
    priority: Optional[str] = None  # 优先级筛选
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


# ---- 并发排期相关 Schema ----

class SetConcurrentRequest(BaseModel):
    """设置并发请求"""
    concurrent_with_task_id: int = Field(..., description="基准任务ID（与哪个任务并发）")


class ExceededUser(BaseModel):
    """并发超限的用户信息"""
    user_id: int
    name: str
    current_concurrent: int
    limit: int


class AffectedSchedule(BaseModel):
    """受影响的排期（串行任务前移）"""
    task_id: int
    task_title: str
    old_scheduled_start: Optional[date]
    new_scheduled_start: Optional[date]


class ConcurrentCheckResponse(BaseModel):
    """并发预检响应"""
    can_set_concurrent: bool
    exceeded_users: List[ExceededUser] = []
    affected_schedules: List[AffectedSchedule] = []


# ---- 个人日程排期 Schema ----

class UserScheduleItem(BaseModel):
    """个人排期条目"""
    task_id: int
    task_title: str
    priority: str
    scheduled_start: Optional[date]
    scheduled_end: Optional[date]
    status: str
    estimated_days: float
    is_concurrent: bool
    concurrent_with: Optional[int]
    role: str  # "assignee" or "collaborator"
    is_pinned: bool = False


class UserScheduleResponse(BaseModel):
    """个人排期响应"""
    schedule: List[UserScheduleItem]


# ---- 项目排期 Schema ----

class ProjectScheduleItem(BaseModel):
    """项目排期条目（供甘特图使用）"""
    task_id: int
    task_title: str
    priority: str
    assignee_id: Optional[int]
    assignee_name: Optional[str]
    scheduled_start: Optional[date]
    scheduled_end: Optional[date]
    status: str
    estimated_man_days: float
    actual_man_days: Optional[float]
    is_concurrent: bool
    deadline: Optional[date]


class ProjectScheduleResponse(BaseModel):
    """项目排期响应"""
    project_id: int
    project_name: str
    tasks: List[ProjectScheduleItem]


# ---- 任务配合人相关 Schema ----

class CollaboratorAdd(BaseModel):
    """添加配合人请求"""
    user_id: int = Field(..., description="配合人用户ID")
    allocated_man_days: Decimal = Field(..., gt=0, description="分配人天数，必须大于0")


class CollaboratorUpdate(BaseModel):
    """更新配合人人天请求"""
    allocated_man_days: Decimal = Field(..., gt=0, description="更新后的分配人天数")


class CollaboratorResponse(BaseModel):
    """配合人响应"""
    id: int
    task_id: int
    user_id: int
    user_name: Optional[str] = None
    user_full_name: Optional[str] = None
    allocated_man_days: Decimal
    scheduled_start: Optional[date] = None
    scheduled_end: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True
