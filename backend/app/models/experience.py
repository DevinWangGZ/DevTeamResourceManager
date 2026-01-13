"""业务履历模型"""
from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from app.models.base import Base


class Experience(Base):
    """业务履历模型"""
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project = Column(String(100), nullable=False, index=True)
    module = Column(String(100))
    role = Column(String(50))
    description = Column(Text)
    man_days = Column(Numeric(10, 2), nullable=False, default=Decimal("0"))  # 投入人天，支持小数
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="experiences")

    def __repr__(self):
        return f"<Experience(id={self.id}, user_id={self.user_id}, project={self.project}, man_days={self.man_days})>"
