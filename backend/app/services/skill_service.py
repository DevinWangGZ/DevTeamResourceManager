"""技能服务"""
from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime

from app.models.skill import Skill
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.schemas.skill import SkillCreate, SkillUpdate


class SkillService:
    """技能服务类"""

    @staticmethod
    def create_skill(db: Session, skill_data: SkillCreate, user_id: int) -> Skill:
        """创建技能"""
        # 检查是否已存在相同技能
        existing_skill = db.query(Skill).filter(
            Skill.user_id == user_id,
            Skill.name == skill_data.name
        ).first()
        
        if existing_skill:
            raise ValidationError(f"技能 '{skill_data.name}' 已存在")

        # 验证熟练度
        valid_proficiencies = ["familiar", "proficient", "expert"]
        if skill_data.proficiency not in valid_proficiencies:
            raise ValidationError(f"熟练度必须是: {', '.join(valid_proficiencies)}")

        skill = Skill(
            user_id=user_id,
            name=skill_data.name,
            proficiency=skill_data.proficiency
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def get_skill(db: Session, skill_id: int, user_id: int) -> Skill:
        """获取技能"""
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise NotFoundError("技能", str(skill_id))
        
        # 权限检查：只能查看自己的技能
        if skill.user_id != user_id:
            raise PermissionDeniedError("只能查看自己的技能")
        
        return skill

    @staticmethod
    def get_user_skills(db: Session, user_id: int) -> List[Skill]:
        """获取用户的所有技能"""
        return db.query(Skill).filter(Skill.user_id == user_id).order_by(Skill.created_at.desc()).all()

    @staticmethod
    def update_skill(
        db: Session,
        skill_id: int,
        skill_data: SkillUpdate,
        user_id: int
    ) -> Skill:
        """更新技能"""
        skill = SkillService.get_skill(db, skill_id, user_id)

        # 如果修改技能名，检查是否与其他技能重复
        if skill_data.name and skill_data.name != skill.name:
            existing_skill = db.query(Skill).filter(
                Skill.user_id == user_id,
                Skill.name == skill_data.name,
                Skill.id != skill_id
            ).first()
            if existing_skill:
                raise ValidationError(f"技能 '{skill_data.name}' 已存在")

        # 验证熟练度
        if skill_data.proficiency:
            valid_proficiencies = ["familiar", "proficient", "expert"]
            if skill_data.proficiency not in valid_proficiencies:
                raise ValidationError(f"熟练度必须是: {', '.join(valid_proficiencies)}")

        # 更新字段
        if skill_data.name is not None:
            skill.name = skill_data.name
        if skill_data.proficiency is not None:
            skill.proficiency = skill_data.proficiency

        db.commit()
        db.refresh(skill)
        return skill

    @staticmethod
    def delete_skill(db: Session, skill_id: int, user_id: int) -> bool:
        """删除技能"""
        skill = SkillService.get_skill(db, skill_id, user_id)
        db.delete(skill)
        db.commit()
        return True
