"""仪表盘API端点"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.dashboard import (
    DeveloperDashboardResponse,
    ProjectManagerDashboardResponse,
    TeamDashboardResponse
)
from app.services.dashboard_service import DashboardService
from app.core.permissions import get_current_development_lead

router = APIRouter()


@router.get("/developer", response_model=DeveloperDashboardResponse)
async def get_developer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取开发人员工作台数据"""
    return DashboardService.get_developer_dashboard(db, current_user.id)


@router.get("/project-manager", response_model=ProjectManagerDashboardResponse)
async def get_project_manager_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目经理仪表盘数据"""
    # 权限检查：只有项目经理可以访问
    if current_user.role not in ["project_manager", "system_admin"]:
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("只有项目经理可以访问项目仪表盘")
    
    return DashboardService.get_project_manager_dashboard(db, current_user.id)


@router.get("/team", response_model=TeamDashboardResponse)
async def get_team_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_development_lead)
):
    """获取开发组长团队仪表盘数据"""
    return DashboardService.get_team_dashboard(db)
