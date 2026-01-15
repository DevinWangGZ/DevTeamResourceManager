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
    # 添加项目名称
    items = []
    for stat in statistics:
        stat_dict = WorkloadStatisticResponse.model_validate(stat).model_dump()
        if stat.project:
            stat_dict['project_name'] = stat.project.name
        items.append(WorkloadStatisticResponse(**stat_dict))
    return WorkloadStatisticListResponse(total=total, items=items)


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
    # 添加项目名称
    items = []
    for stat in statistics:
        stat_dict = WorkloadStatisticResponse.model_validate(stat).model_dump()
        if stat.project:
            stat_dict['project_name'] = stat.project.name
        items.append(WorkloadStatisticResponse(**stat_dict))
    return WorkloadStatisticListResponse(total=len(items), items=items)


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
    # 添加项目名称
    items = []
    for stat in statistics:
        stat_dict = WorkloadStatisticResponse.model_validate(stat).model_dump()
        if stat.project:
            stat_dict['project_name'] = stat.project.name
        items.append(WorkloadStatisticResponse(**stat_dict))
    return WorkloadStatisticListResponse(total=len(items), items=items)


@router.get("/workload", response_model=dict)
async def get_workload_timeline(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的工作负荷时间轴数据（基于任务排期）
    
    工作负荷基于已认领/进行中任务的排期和拟投入人天
    """
    from app.models.task import Task, TaskStatus
    from app.models.task_schedule import TaskSchedule
    from app.services.schedule_service import ScheduleService
    from sqlalchemy.orm import joinedload
    from datetime import timedelta
    from decimal import Decimal
    
    # 默认查询最近4周的数据
    today = date.today()
    if not start_date:
        start_date = today - timedelta(days=28)
    if not end_date:
        end_date = today + timedelta(days=30)  # 包含未来30天
    
    # 获取用户的任务排期
    schedules = ScheduleService.get_user_schedules(
        db,
        current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 获取关联的任务信息
    task_ids = [s.task_id for s in schedules]
    
    # 如果没有任务排期，直接返回空结果，避免不必要的数据库查询
    if not task_ids:
        return {
            "total": 0,
            "items": []
        }
    
    tasks = db.query(Task).options(
        joinedload(Task.project)
    ).filter(
        Task.id.in_(task_ids),
        Task.status.in_([TaskStatus.CLAIMED.value, TaskStatus.IN_PROGRESS.value])
    ).all()
    
    # 构建任务字典
    task_dict = {task.id: task for task in tasks}
    
    # 按周组织数据（使用ISO周）
    workload_by_week = {}
    
    for schedule in schedules:
        if schedule.task_id not in task_dict:
            continue
        
        task = task_dict[schedule.task_id]
        if not schedule.start_date or not schedule.end_date:
            continue
        
        # 计算工作日数量
        work_days = ScheduleService.get_workdays_count(
            schedule.start_date,
            schedule.end_date,
            db
        )
        
        if work_days == 0:
            continue
        
        # 计算每天的平均工作量（拟投入人天 / 工作日数）
        estimated_man_days = float(task.estimated_man_days) if task.estimated_man_days else 0
        daily_workload = estimated_man_days / work_days if work_days > 0 else 0
        
        # 遍历排期期间的每一天
        current_date = schedule.start_date
        while current_date <= schedule.end_date and current_date <= end_date:
            # 跳过周末和节假日
            if ScheduleService.is_workday(current_date, db):
                # 按ISO周组织
                iso_year, iso_week, iso_weekday = current_date.isocalendar()
                week_key = f"{iso_year}-W{iso_week:02d}"
                
                # 初始化周数据
                if week_key not in workload_by_week:
                    # 计算该周的开始日期（周一）
                    week_start = current_date - timedelta(days=iso_weekday - 1)
                    workload_by_week[week_key] = {
                        "period_start": week_start.isoformat(),
                        "period_end": week_start.isoformat(),
                        "total_man_days": Decimal("0"),
                        "tasks": []
                    }
                
                # 累加工作量
                workload_by_week[week_key]["total_man_days"] += Decimal(str(daily_workload))
                
                # 更新周期结束日期
                if current_date > date.fromisoformat(workload_by_week[week_key]["period_end"]):
                    workload_by_week[week_key]["period_end"] = current_date.isoformat()
                
                # 添加任务信息（避免重复）
                task_info = {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "estimated_man_days": estimated_man_days
                }
                # 检查任务是否已存在
                task_exists = any(t["id"] == task.id for t in workload_by_week[week_key]["tasks"])
                if not task_exists:
                    workload_by_week[week_key]["tasks"].append(task_info)
            
            current_date += timedelta(days=1)
    
    # 转换为列表格式，按周期开始日期排序
    items = []
    for period_key, period_data in sorted(workload_by_week.items()):
        items.append({
            "period_start": period_data["period_start"],
            "period_end": period_data["period_end"],
            "total_man_days": float(period_data["total_man_days"]),
            "tasks": period_data["tasks"]
        })
    
    return {
        "total": len(items),
        "items": items
    }


@router.get("/trend", response_model=dict)
async def get_workload_trend(
    period_type: str = Query("month", description="时间维度: month/week"),
    months: int = Query(6, ge=1, le=12, description="查询月数（仅当period_type=month时有效）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的工作量趋势数据
    
    按时间维度（月/周）聚合工作量统计数据
    """
    from datetime import timedelta
    from decimal import Decimal
    
    today = date.today()
    trend_data = []
    
    if period_type == "month":
        # 按月统计
        for i in range(months - 1, -1, -1):
            target_month = today.month - i
            target_year = today.year
            
            # 处理跨年
            while target_month < 1:
                target_month += 12
                target_year -= 1
            
            month_start = date(target_year, target_month, 1)
            if target_month == 12:
                month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(target_year, target_month + 1, 1) - timedelta(days=1)
            
            # 获取该月的工作量统计
            statistics = WorkloadStatisticService.get_user_statistics(
                db,
                current_user.id,
                period_start=month_start,
                period_end=month_end
            )
            
            # 汇总该月的总工作量
            total_man_days = Decimal("0")
            for stat in statistics:
                total_man_days += stat.total_man_days
            
            trend_data.append({
                "period": f"{target_year}-{target_month:02d}",
                "period_start": month_start.isoformat(),
                "period_end": month_end.isoformat(),
                "total_man_days": float(total_man_days),
            })
    
    elif period_type == "week":
        # 按周统计（最近12周）
        for i in range(11, -1, -1):
            week_start = today - timedelta(days=today.weekday() + i * 7)
            week_end = week_start + timedelta(days=6)
            
            # 获取该周的工作量统计
            statistics = WorkloadStatisticService.get_user_statistics(
                db,
                current_user.id,
                period_start=week_start,
                period_end=week_end
            )
            
            # 汇总该周的总工作量
            total_man_days = Decimal("0")
            for stat in statistics:
                # 只计算与周期重叠的部分
                stat_start = max(stat.period_start, week_start)
                stat_end = min(stat.period_end, week_end)
                if stat_start <= stat_end:
                    # 按重叠天数比例计算工作量
                    overlap_days = (stat_end - stat_start).days + 1
                    stat_days = (stat.period_end - stat.period_start).days + 1
                    if stat_days > 0:
                        ratio = Decimal(str(overlap_days)) / Decimal(str(stat_days))
                        total_man_days += stat.total_man_days * ratio
            
            trend_data.append({
                "period": f"{week_start.year}-W{week_start.isocalendar()[1]:02d}",
                "period_start": week_start.isoformat(),
                "period_end": week_end.isoformat(),
                "total_man_days": float(total_man_days),
            })
    
    return {
        "period_type": period_type,
        "total": len(trend_data),
        "items": trend_data
    }
