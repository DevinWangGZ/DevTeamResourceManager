"""消息通知API端点"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.message import MessageResponse, MessageListResponse, MessageUnreadCountResponse
from app.services.message_service import MessageService
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/", response_model=MessageListResponse)
async def get_messages(
    type: Optional[str] = Query(None, description="消息类型"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的消息列表"""
    skip = (page - 1) * page_size
    messages, total = MessageService.get_messages(
        db,
        user_id=current_user.id,
        message_type=type,
        is_read=is_read,
        skip=skip,
        limit=page_size
    )

    items = [MessageResponse.model_validate(msg) for msg in messages]

    return MessageListResponse(total=total, items=items)


@router.get("/unread-count", response_model=MessageUnreadCountResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的未读消息数量"""
    count = MessageService.get_unread_count(db, current_user.id)
    return MessageUnreadCountResponse(unread_count=count)


@router.post("/{message_id}/read")
async def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记消息为已读"""
    try:
        message = MessageService.mark_as_read(db, message_id, current_user.id)
        return MessageResponse.model_validate(message)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/read-all")
async def mark_all_as_read(
    type: Optional[str] = Query(None, description="消息类型（可选）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记所有消息为已读"""
    count = MessageService.mark_all_as_read(db, current_user.id, message_type=type)
    return {"message": f"已标记 {count} 条消息为已读"}


@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除消息"""
    try:
        MessageService.delete_message(db, message_id, current_user.id)
        return {"message": "消息已删除"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
