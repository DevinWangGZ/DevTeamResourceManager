"""节假日模型"""
from sqlalchemy import Column, Integer, Date, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func

from app.models.base import Base


class Holiday(Base):
    """节假日模型"""
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    description = Column(String(200))  # 节假日描述，如：春节、国庆节
    is_weekend = Column(Boolean, nullable=False, default=False)  # 是否为周末
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<Holiday(id={self.id}, date={self.date}, description={self.description})>"
