"""仪表盘相关模式"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal


class TaskSummary(BaseModel):
    """任务汇总"""
    total: int = Field(..., description="总任务数")
    in_progress: int = Field(..., description="进行中")
    submitted: int = Field(..., description="已提交")
    confirmed: int = Field(..., description="已确认")
    pending_eval: int = Field(..., description="待评估")


class WorkloadSummary(BaseModel):
    """工作量汇总"""
    total_man_days: Decimal = Field(..., description="总投入人天")
    project_count: int = Field(..., description="参与项目数")
    period_start: Optional[date] = Field(None, description="统计周期开始")
    period_end: Optional[date] = Field(None, description="统计周期结束")


class TodoReminder(BaseModel):
    """待办提醒"""
    type: str = Field(..., description="提醒类型")
    title: str = Field(..., description="提醒标题")
    count: int = Field(..., description="数量")
    link: Optional[str] = Field(None, description="跳转链接")


class DeveloperDashboardResponse(BaseModel):
    """开发人员工作台响应"""
    task_summary: TaskSummary = Field(..., description="任务汇总")
    workload_summary: Optional[WorkloadSummary] = Field(None, description="工作量汇总")
    todo_reminders: List[TodoReminder] = Field(default_factory=list, description="待办提醒")
    recent_tasks: List[dict] = Field(default_factory=list, description="最近任务")


class ProjectTaskSummary(BaseModel):
    """项目任务汇总"""
    project_id: int
    project_name: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_confirmation: int


class ProjectOutputSummary(BaseModel):
    """项目产值汇总"""
    project_id: int
    project_name: str
    estimated_value: Decimal = Field(..., description="预计产值")
    task_output_value: Decimal = Field(..., description="任务产值")
    allocated_output_value: Decimal = Field(..., description="已分配产值")
    is_over_budget: bool = Field(..., description="是否超出预算")


class ProjectManagerDashboardResponse(BaseModel):
    """项目经理仪表盘响应"""
    project_summaries: List[ProjectTaskSummary] = Field(default_factory=list, description="项目任务汇总")
    output_summaries: List[ProjectOutputSummary] = Field(default_factory=list, description="项目产值汇总")
    pending_confirmation_count: int = Field(..., description="待确认任务数")
    todo_reminders: List[TodoReminder] = Field(default_factory=list, description="待办提醒")


class TeamMemberSummary(BaseModel):
    """团队成员汇总"""
    user_id: int
    username: str
    full_name: Optional[str]
    workload_status: str = Field(..., description="负荷状态: overloaded/normal/idle")
    total_man_days: Decimal = Field(..., description="总投入人天")
    active_tasks: int = Field(..., description="进行中任务数")


class TeamDashboardResponse(BaseModel):
    """开发组长团队仪表盘响应"""
    total_members: int = Field(..., description="团队成员数")
    total_workload: Decimal = Field(..., description="团队总工作量")
    task_completion_rate: Decimal = Field(..., description="任务完成率")
    member_summaries: List[TeamMemberSummary] = Field(default_factory=list, description="成员汇总")
    todo_reminders: List[TodoReminder] = Field(default_factory=list, description="待办提醒")
