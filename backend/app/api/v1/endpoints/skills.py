"""技能管理API端点"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse
)
from app.services.skill_service import SkillService

router = APIRouter()


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(
    skill_data: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建技能"""
    skill = SkillService.create_skill(db, skill_data, current_user.id)
    return skill


@router.get("/", response_model=SkillListResponse)
async def get_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有技能"""
    skills = SkillService.get_user_skills(db, current_user.id)
    return SkillListResponse(total=len(skills), items=skills)


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取技能详情"""
    skill = SkillService.get_skill(db, skill_id, current_user.id)
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新技能"""
    skill = SkillService.update_skill(db, skill_id, skill_data, current_user.id)
    return skill


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除技能"""
    SkillService.delete_skill(db, skill_id, current_user.id)
    return None
