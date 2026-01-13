"""业务履历管理API端点"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.experience import (
    ExperienceCreate,
    ExperienceUpdate,
    ExperienceResponse,
    ExperienceListResponse
)
from app.services.experience_service import ExperienceService

router = APIRouter()


@router.post("/", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    experience_data: ExperienceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建业务履历"""
    experience = ExperienceService.create_experience(db, experience_data, current_user.id)
    return experience


@router.get("/", response_model=ExperienceListResponse)
async def get_experiences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有业务履历"""
    experiences = ExperienceService.get_user_experiences(db, current_user.id)
    return ExperienceListResponse(total=len(experiences), items=experiences)


@router.get("/{experience_id}", response_model=ExperienceResponse)
async def get_experience(
    experience_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取业务履历详情"""
    experience = ExperienceService.get_experience(db, experience_id, current_user.id)
    return experience


@router.put("/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: int,
    experience_data: ExperienceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新业务履历"""
    experience = ExperienceService.update_experience(db, experience_id, experience_data, current_user.id)
    return experience


@router.delete("/{experience_id}", status_code=204)
async def delete_experience(
    experience_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除业务履历"""
    ExperienceService.delete_experience(db, experience_id, current_user.id)
    return None
