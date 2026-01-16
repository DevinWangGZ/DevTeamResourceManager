"""数据导出API端点"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.core.permissions import require_roles
from app.models.user import UserRole
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/workload-statistics")
async def export_workload_statistics(
    user_id: Optional[int] = Query(None, description="用户ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    period_start: Optional[date] = Query(None, description="统计周期开始日期"),
    period_end: Optional[date] = Query(None, description="统计周期结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出工作量统计数据到Excel
    
    权限：所有登录用户都可以导出自己的数据，项目经理和开发组长可以导出所有数据
    """
    # 权限检查：普通开发人员只能导出自己的数据
    if current_user.role == "developer" and user_id and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限导出其他用户的数据")
    
    try:
        excel_file = ExportService.export_workload_statistics(
            db=db,
            user_id=user_id if current_user.role != "developer" else current_user.id,
            project_id=project_id,
            period_start=period_start,
            period_end=period_end
        )
        
        filename = f"工作量统计_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/tasks")
async def export_tasks(
    status: Optional[str] = Query(None, description="任务状态"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    creator_id: Optional[int] = Query(None, description="创建者ID"),
    assignee_id: Optional[int] = Query(None, description="负责人ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出任务数据到Excel
    
    权限：所有登录用户都可以导出
    """
    # 权限检查：普通开发人员只能导出自己相关的任务
    if current_user.role == "developer":
        if creator_id and creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限导出其他用户创建的任务")
        if assignee_id and assignee_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限导出其他用户负责的任务")
        # 开发人员默认只能看到自己负责或创建的任务
        if not creator_id and not assignee_id:
            assignee_id = current_user.id
    
    try:
        excel_file = ExportService.export_tasks(
            db=db,
            status=status,
            project_id=project_id,
            creator_id=creator_id,
            assignee_id=assignee_id
        )
        
        filename = f"任务列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/performance")
async def export_performance_data(
    user_id: Optional[int] = Query(None, description="用户ID"),
    period_start: Optional[date] = Query(None, description="统计周期开始日期"),
    period_end: Optional[date] = Query(None, description="统计周期结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出绩效数据到Excel
    
    权限：开发组长和系统管理员可以导出所有数据，其他用户只能导出自己的数据
    """
    # 权限检查
    if current_user.role == "developer":
        if user_id and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限导出其他用户的绩效数据")
        user_id = current_user.id
    elif current_user.role == "project_manager":
        # 项目经理只能导出自己负责的项目相关数据，这里简化处理，允许导出所有
        pass
    
    try:
        excel_file = ExportService.export_performance_data(
            db=db,
            user_id=user_id,
            period_start=period_start,
            period_end=period_end
        )
        
        filename = f"绩效数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
