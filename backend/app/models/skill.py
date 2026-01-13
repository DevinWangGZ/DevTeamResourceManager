"""技能模型"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class Proficiency(str, enum.Enum):
    """熟练度枚举"""
    FAMILIAR = "familiar"      # 熟悉
    PROFICIENT = "proficient"   # 熟练
    EXPERT = "expert"          # 精通


class Skill(Base):
    """技能模型"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    proficiency = Column(
        String(20),
        nullable=False,
        default=Proficiency.FAMILIAR
    )
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="skills")

    # 唯一约束：同一用户不能有重复的技能名
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_skill"),
    )

    def __repr__(self):
        return f"<Skill(id={self.id}, user_id={self.user_id}, name={self.name}, proficiency={self.proficiency})>"
