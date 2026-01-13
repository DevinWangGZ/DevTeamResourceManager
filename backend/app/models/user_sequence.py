"""序列管理模型"""
from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from app.models.base import Base


class UserSequence(Base):
    """用户序列管理模型"""
    __tablename__ = "user_sequences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(50), nullable=False)  # 序列等级，如：初级开发、中级开发、高级开发
    unit_price = Column(Numeric(10, 2), nullable=False)  # 单价（元/人天）
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="user_sequences")

    # 唯一约束：同一用户不能有重复的序列等级
    __table_args__ = (
        UniqueConstraint("user_id", "level", name="uq_user_sequence"),
    )

    def __repr__(self):
        return f"<UserSequence(id={self.id}, user_id={self.user_id}, level={self.level}, unit_price={self.unit_price})>"
