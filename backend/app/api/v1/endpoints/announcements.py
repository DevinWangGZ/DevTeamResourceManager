"""系统公告 API 端点"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.core.permissions import get_current_admin
from app.models.user import User
from app.models.announcement import Announcement
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse,
)

router = APIRouter()


def _build_response(ann: Announcement) -> AnnouncementResponse:
    resp = AnnouncementResponse.model_validate(ann)
    if ann.author:
        resp.author_name = ann.author.full_name or ann.author.username
    return resp


@router.get("", response_model=AnnouncementListResponse, summary="获取公告列表（所有用户可见）")
async def list_announcements(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取公告列表。
    - 普通用户只看到已启用的公告。
    - 管理员可通过 include_inactive=true 看到所有公告（含已禁用）。
    """
    query = db.query(Announcement)
    # 非管理员只能看启用的公告
    user_role_codes = [r.code for r in current_user.roles] if current_user.roles else []
    is_admin = "system_admin" in user_role_codes or current_user.role == "system_admin"
    if not (is_admin and include_inactive):
        query = query.filter(Announcement.is_active == True)

    announcements = query.order_by(Announcement.created_at.desc()).all()
    return AnnouncementListResponse(
        total=len(announcements),
        items=[_build_response(a) for a in announcements],
    )


@router.post("", response_model=AnnouncementResponse, summary="创建公告（仅系统管理员）")
async def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """创建系统公告，仅系统管理员可操作。"""
    valid_priorities = {"normal", "important", "urgent"}
    if data.priority not in valid_priorities:
        raise HTTPException(status_code=422, detail="priority 只能为 normal / important / urgent")

    ann = Announcement(
        title=data.title,
        content=data.content,
        priority=data.priority,
        is_active=data.is_active,
        author_id=current_user.id,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return _build_response(ann)


@router.put("/{announcement_id}", response_model=AnnouncementResponse, summary="更新公告（仅系统管理员）")
async def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """更新公告内容或状态，仅系统管理员可操作。"""
    ann = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")

    if data.title is not None:
        ann.title = data.title
    if data.content is not None:
        ann.content = data.content
    if data.priority is not None:
        valid_priorities = {"normal", "important", "urgent"}
        if data.priority not in valid_priorities:
            raise HTTPException(status_code=422, detail="priority 只能为 normal / important / urgent")
        ann.priority = data.priority
    if data.is_active is not None:
        ann.is_active = data.is_active

    db.commit()
    db.refresh(ann)
    return _build_response(ann)


@router.delete("/{announcement_id}", summary="删除公告（仅系统管理员）")
async def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """删除公告，仅系统管理员可操作。"""
    ann = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(ann)
    db.commit()
    return {"message": "公告已删除"}
