"""业务履历服务"""
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.models.experience import Experience
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.schemas.experience import ExperienceCreate, ExperienceUpdate


class ExperienceService:
    """业务履历服务类"""

    @staticmethod
    def create_experience(db: Session, experience_data: ExperienceCreate, user_id: int) -> Experience:
        """创建业务履历"""
        experience = Experience(
            user_id=user_id,
            project=experience_data.project,
            module=experience_data.module,
            role=experience_data.role,
            description=experience_data.description,
            man_days=experience_data.man_days
        )
        db.add(experience)
        db.commit()
        db.refresh(experience)
        return experience

    @staticmethod
    def get_experience(db: Session, experience_id: int, user_id: int) -> Experience:
        """获取业务履历"""
        experience = db.query(Experience).filter(Experience.id == experience_id).first()
        if not experience:
            raise NotFoundError("业务履历", str(experience_id))
        
        # 权限检查：只能查看自己的履历
        if experience.user_id != user_id:
            raise PermissionDeniedError("只能查看自己的业务履历")
        
        return experience

    @staticmethod
    def get_user_experiences(db: Session, user_id: int) -> List[Experience]:
        """获取用户的所有业务履历"""
        return db.query(Experience).filter(Experience.user_id == user_id).order_by(Experience.created_at.desc()).all()

    @staticmethod
    def update_experience(
        db: Session,
        experience_id: int,
        experience_data: ExperienceUpdate,
        user_id: int
    ) -> Experience:
        """更新业务履历"""
        experience = ExperienceService.get_experience(db, experience_id, user_id)

        # 更新字段
        if experience_data.project is not None:
            experience.project = experience_data.project
        if experience_data.module is not None:
            experience.module = experience_data.module
        if experience_data.role is not None:
            experience.role = experience_data.role
        if experience_data.description is not None:
            experience.description = experience_data.description
        if experience_data.man_days is not None:
            experience.man_days = experience_data.man_days

        db.commit()
        db.refresh(experience)
        return experience

    @staticmethod
    def delete_experience(db: Session, experience_id: int, user_id: int) -> bool:
        """删除业务履历"""
        experience = ExperienceService.get_experience(db, experience_id, user_id)
        db.delete(experience)
        db.commit()
        return True
