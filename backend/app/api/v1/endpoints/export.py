"""数据导出API端点"""
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from app.api.deps import get_db, get_current_user
from app.core.exceptions import AppException
from app.models.task import TaskStatus
from app.models.user import User
from app.schemas.task import TaskFilterParams
from app.services.export_service import ExportService

router = APIRouter()


def _attachment_headers(filename_utf8: str, filename_ascii_fallback: str) -> dict[str, str]:
    """RFC 5987：非 ASCII 文件名用 filename*，避免响应头 Latin-1 编码错误。"""
    disp = (
        f'attachment; filename="{filename_ascii_fallback}"; '
        f"filename*=UTF-8''{quote(filename_utf8, safe='')}"
    )
    return {"Content-Disposition": disp}


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
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"工作量统计_{ts}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=_attachment_headers(filename, f"workload_statistics_{ts}.xlsx"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/tasks")
async def export_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态"),
    statuses: Optional[str] = Query(None, description="任务状态多选（逗号分隔）"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    project_ids: Optional[str] = Query(None, description="项目ID多选（逗号分隔）"),
    creator_id: Optional[int] = Query(None, description="创建者ID"),
    creator_ids: Optional[str] = Query(None, description="创建者ID多选（逗号分隔）"),
    assignee_id: Optional[int] = Query(None, description="认领者ID"),
    assignee_ids: Optional[str] = Query(None, description="认领者ID多选（逗号分隔）"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题或描述）"),
    required_skills: Optional[str] = Query(None, description="所需技能（逗号分隔）"),
    priority: Optional[str] = Query(None, description="优先级筛选：P0/P1/P2"),
    embed_images: bool = Query(False, description="是否嵌入问题图片到Excel，默认false"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    导出任务数据到 Excel。

    - 不传 project_id：筛选与 GET /tasks 一致（开发人员对应列表可见范围）。
    - 仅带 project_id 且不带 project_ids：与同项目 GET /projects/{project_id}/tasks 一致，
      避免页面看到整项目任务但导出却只有「列表级」数量的记录。
    """

    def parse_csv_ints(value: Optional[str]) -> Optional[list[int]]:
        if not value:
            return None
        result = []
        for raw in value.split(","):
            item = raw.strip()
            if not item:
                continue
            try:
                result.append(int(item))
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=f"非法ID: {item}") from exc
        return result or None

    def parse_csv_statuses(value: Optional[str]) -> Optional[list[TaskStatus]]:
        if not value:
            return None
        allowed = {s.value: s for s in TaskStatus}
        result = []
        for raw in value.split(","):
            item = raw.strip()
            if not item:
                continue
            if item not in allowed:
                raise HTTPException(status_code=422, detail=f"非法任务状态: {item}")
            result.append(allowed[item])
        return result or None

    filters = TaskFilterParams(
        status=status,
        statuses=parse_csv_statuses(statuses),
        project_id=project_id,
        project_ids=parse_csv_ints(project_ids),
        creator_id=creator_id,
        creator_ids=parse_csv_ints(creator_ids),
        assignee_id=assignee_id,
        assignee_ids=parse_csv_ints(assignee_ids),
        keyword=keyword,
        required_skills=required_skills,
        priority=priority,
        page=1,
        page_size=100,
    )

    try:
        excel_file = ExportService.export_tasks(
            db,
            filters=filters,
            current_user_id=current_user.id,
            current_user_role=current_user.role,
            embed_images=embed_images,
        )
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"任务列表_{ts}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=_attachment_headers(filename, f"tasks_{ts}.xlsx"),
        )
    except AppException:
        raise
    except HTTPException:
        raise
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
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"绩效数据_{ts}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=_attachment_headers(filename, f"performance_{ts}.xlsx"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
