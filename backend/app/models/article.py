"""知识分享模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Integer as Int, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Article(Base):
    """知识分享模型"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # Markdown格式内容
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(50))  # 分类
    tags = Column(Text)  # 标签（JSON格式或逗号分隔）
    is_published = Column(Boolean, nullable=False, default=False, index=True)  # 是否发布
    view_count = Column(Int, nullable=False, default=0)  # 浏览次数
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    # 关系
    author = relationship("User", back_populates="articles")

    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title}, author_id={self.author_id}, is_published={self.is_published})>"
