"""用户序列管理API端点"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user_sequence import (
    UserSequenceCreate,
    UserSequenceUpdate,
    UserSequenceResponse,
    UserSequenceListResponse
)
from app.services.user_sequence_service import UserSequenceService

router = APIRouter()


@router.post("/", response_model=UserSequenceResponse, status_code=201)
async def create_user_sequence(
    sequence_data: UserSequenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户序列"""
    sequence = UserSequenceService.create_user_sequence(db, sequence_data, current_user.id)
    return sequence


@router.get("/", response_model=UserSequenceListResponse)
async def get_user_sequences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有序列"""
    sequences = UserSequenceService.get_user_sequences(db, current_user.id)
    return UserSequenceListResponse(total=len(sequences), items=sequences)


@router.get("/{sequence_id}", response_model=UserSequenceResponse)
async def get_user_sequence(
    sequence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户序列详情"""
    sequence = UserSequenceService.get_user_sequence(db, sequence_id, current_user.id)
    return sequence


@router.put("/{sequence_id}", response_model=UserSequenceResponse)
async def update_user_sequence(
    sequence_id: int,
    sequence_data: UserSequenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户序列"""
    sequence = UserSequenceService.update_user_sequence(db, sequence_id, sequence_data, current_user.id)
    return sequence


@router.delete("/{sequence_id}", status_code=204)
async def delete_user_sequence(
    sequence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户序列"""
    UserSequenceService.delete_user_sequence(db, sequence_id, current_user.id)
    return None
