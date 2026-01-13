"""用户序列服务"""
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.models.user_sequence import UserSequence
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.schemas.user_sequence import UserSequenceCreate, UserSequenceUpdate


class UserSequenceService:
    """用户序列服务类"""

    @staticmethod
    def create_user_sequence(db: Session, sequence_data: UserSequenceCreate, user_id: int) -> UserSequence:
        """创建用户序列"""
        # 检查是否已存在相同等级的序列
        existing_sequence = db.query(UserSequence).filter(
            UserSequence.user_id == user_id,
            UserSequence.level == sequence_data.level
        ).first()
        
        if existing_sequence:
            raise ValidationError(f"序列等级 '{sequence_data.level}' 已存在")

        sequence = UserSequence(
            user_id=user_id,
            level=sequence_data.level,
            unit_price=sequence_data.unit_price
        )
        db.add(sequence)
        db.commit()
        db.refresh(sequence)
        return sequence

    @staticmethod
    def get_user_sequence(db: Session, sequence_id: int, user_id: int) -> UserSequence:
        """获取用户序列"""
        sequence = db.query(UserSequence).filter(UserSequence.id == sequence_id).first()
        if not sequence:
            raise NotFoundError("用户序列", str(sequence_id))
        
        # 权限检查：只能查看自己的序列
        if sequence.user_id != user_id:
            raise PermissionDeniedError("只能查看自己的序列信息")
        
        return sequence

    @staticmethod
    def get_user_sequences(db: Session, user_id: int) -> List[UserSequence]:
        """获取用户的所有序列"""
        return db.query(UserSequence).filter(UserSequence.user_id == user_id).order_by(UserSequence.created_at.desc()).all()

    @staticmethod
    def get_user_sequence_by_level(db: Session, user_id: int, level: str) -> Optional[UserSequence]:
        """根据等级获取用户序列"""
        return db.query(UserSequence).filter(
            UserSequence.user_id == user_id,
            UserSequence.level == level
        ).first()

    @staticmethod
    def update_user_sequence(
        db: Session,
        sequence_id: int,
        sequence_data: UserSequenceUpdate,
        user_id: int
    ) -> UserSequence:
        """更新用户序列"""
        sequence = UserSequenceService.get_user_sequence(db, sequence_id, user_id)

        # 如果修改等级，检查是否与其他序列重复
        if sequence_data.level and sequence_data.level != sequence.level:
            existing_sequence = db.query(UserSequence).filter(
                UserSequence.user_id == user_id,
                UserSequence.level == sequence_data.level,
                UserSequence.id != sequence_id
            ).first()
            if existing_sequence:
                raise ValidationError(f"序列等级 '{sequence_data.level}' 已存在")

        # 更新字段
        if sequence_data.level is not None:
            sequence.level = sequence_data.level
        if sequence_data.unit_price is not None:
            sequence.unit_price = sequence_data.unit_price

        db.commit()
        db.refresh(sequence)
        return sequence

    @staticmethod
    def delete_user_sequence(db: Session, sequence_id: int, user_id: int) -> bool:
        """删除用户序列"""
        sequence = UserSequenceService.get_user_sequence(db, sequence_id, user_id)
        db.delete(sequence)
        db.commit()
        return True
