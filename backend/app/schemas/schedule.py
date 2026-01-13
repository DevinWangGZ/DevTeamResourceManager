"""排期相关模式"""
from pydantic import BaseModel
from datetime import date


class TaskScheduleResponse(BaseModel):
    """任务排期响应"""
    id: int
    task_id: int
    start_date: date
    end_date: date
    is_pinned: bool
    work_days: int  # 工作日数量

    class Config:
        from_attributes = True
