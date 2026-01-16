"""文章附件模型"""
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class ArticleAttachment(Base):
    """文章附件模型"""
    __tablename__ = "article_attachments"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 文件存储路径（相对路径）
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_type = Column(String(50), nullable=False)  # 文件类型（word、ppt、pdf、excel）
    mime_type = Column(String(100), nullable=False)  # MIME类型
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # 关系
    article = relationship("Article", back_populates="attachments")

    def __repr__(self):
        return f"<ArticleAttachment(id={self.id}, article_id={self.article_id}, filename={self.filename})>"
