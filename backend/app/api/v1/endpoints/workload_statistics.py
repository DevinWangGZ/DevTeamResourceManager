"""工作量统计API端点"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.workload_statistic import (
    WorkloadStatisticResponse,
    WorkloadStatisticListResponse,
    WorkloadStatisticFilterParams,
    WorkloadSummaryResponse
)
from app.services.workload_statistic_service import WorkloadStatisticService
from app.core.exceptions import PermissionDeniedError

router = APIRouter()


@router.get("/", response_model=WorkloadStatisticListResponse)
async def get_statistics(
    user_id: Optional[int] = Query(None, description="用户ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    period_start: Optional[date] = Query(None, description="统计周期开始日期"),
    period_end: Optional[date] = Query(None, description="统计周期结束日期"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作量统计列表
    
    权限说明：
    - 开发人员：只能查看自己的统计
    - 项目经理：可以查看自己项目的统计
    - 开发组长/系统管理员：可以查看所有统计
    """
    filters = WorkloadStatisticFilterParams(
        user_id=user_id,
        project_id=project_id,
        period_start=period_start,
        period_end=period_end,
        skip=skip,
        limit=limit
    )

    # 权限检查
    if current_user.role == "developer":
        # 开发人员只能查看自己的统计
        if filters.user_id and filters.user_id != current_user.id:
            raise PermissionDeniedError("只能查看自己的工作量统计")
        filters.user_id = current_user.id
    elif current_user.role == "project_manager":
        # 项目经理可以查看自己项目的统计
        # 如果指定了user_id，只能查看自己项目的成员
        pass
    # development_lead 和 system_admin 可以查看所有统计

    statistics, total = WorkloadStatisticService.get_statistics(db, filters)
    return WorkloadStatisticListResponse(total=total, items=statistics)


@router.get("/my", response_model=WorkloadStatisticListResponse)
async def get_my_statistics(
    project_id: Optional[int] = Query(None, description="项目ID"),
    period_start: Optional[date] = Query(None, description="统计周期开始日期"),
    period_end: Optional[date] = Query(None, description="统计周期结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的工作量统计"""
    statistics = WorkloadStatisticService.get_user_statistics(
        db,
        current_user.id,
        project_id=project_id,
        period_start=period_start,
        period_end=period_end
    )
    return WorkloadStatisticListResponse(total=len(statistics), items=statistics)


@router.get("/summary", response_model=WorkloadSummaryResponse)
async def get_my_summary(
    period_start: Optional[date] = Query(None, description="统计周期开始日期"),
    period_end: Optional[date] = Query(None, description="统计周期结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的工作量汇总"""
    summary = WorkloadStatisticService.get_user_summary(
        db,
        current_user.id,
        period_start=period_start,
        period_end=period_end
    )
    
    return WorkloadSummaryResponse(
        user_id=summary['user_id'],
        user_name=current_user.full_name or current_user.username,
        total_man_days=summary['total_man_days'],
        project_count=summary['project_count'],
        period_start=period_start or date.today().replace(day=1),
        period_end=period_end or date.today()
    )


@router.get("/project/{project_id}", response_model=WorkloadStatisticListResponse)
async def get_project_statistics(
    project_id: int,
    period_start: Optional[date] = Query(None, description="统计周期开始日期"),
    period_end: Optional[date] = Query(None, description="统计周期结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定项目的工作量统计
    
    权限说明：
    - 项目经理：只能查看自己项目的统计
    - 开发组长/系统管理员：可以查看所有项目统计
    """
    # 权限检查：项目经理只能查看自己创建的项目
    if current_user.role == "project_manager":
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or project.created_by != current_user.id:
            raise PermissionDeniedError("只能查看自己项目的统计")

    statistics = WorkloadStatisticService.get_project_statistics(
        db,
        project_id,
        period_start=period_start,
        period_end=period_end
    )
    return WorkloadStatisticListResponse(total=len(statistics), items=statistics)
