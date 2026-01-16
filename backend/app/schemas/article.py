"""知识分享相关模式"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ArticleBase(BaseModel):
    """文章基础模式"""
    title: str = Field(..., max_length=200, description="文章标题")
    content: str = Field(..., description="文章内容（Markdown格式）")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    tags: Optional[str] = Field(None, description="标签（逗号分隔）")
    is_published: bool = Field(False, description="是否发布")


class ArticleCreate(ArticleBase):
    """创建文章请求"""
    pass


class ArticleUpdate(BaseModel):
    """更新文章请求"""
    title: Optional[str] = Field(None, max_length=200, description="文章标题")
    content: Optional[str] = Field(None, description="文章内容（Markdown格式）")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    tags: Optional[str] = Field(None, description="标签（逗号分隔）")
    is_published: Optional[bool] = Field(None, description="是否发布")


class ArticleResponse(ArticleBase):
    """文章响应"""
    id: int
    author_id: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    author_name: Optional[str] = None
    author_full_name: Optional[str] = None
    attachments: Optional[List["ArticleAttachmentResponse"]] = None

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """文章列表响应"""
    total: int
    items: List[ArticleResponse]


class ArticleSearchParams(BaseModel):
    """文章搜索参数"""
    keyword: Optional[str] = Field(None, description="关键词（搜索标题和内容）")
    category: Optional[str] = Field(None, description="分类")
    tag: Optional[str] = Field(None, description="标签")
    author_id: Optional[int] = Field(None, description="作者ID")
    is_published: Optional[bool] = Field(None, description="是否发布")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class CategoryResponse(BaseModel):
    """分类响应"""
    name: str
    count: int


class TagResponse(BaseModel):
    """标签响应"""
    name: str
    count: int


class ArticleAttachmentResponse(BaseModel):
    """文章附件响应"""
    id: int
    article_id: int
    filename: str
    file_path: str
    file_size: int
    file_type: str
    mime_type: str
    created_at: datetime

    class Config:
        from_attributes = True
