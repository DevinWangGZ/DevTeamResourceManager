"""知识分享API端点"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.article import (
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListResponse,
    CategoryResponse,
    TagResponse,
    ArticleAttachmentResponse
)
from app.services.article_service import ArticleService
from app.models.article_attachment import ArticleAttachment
from app.core.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter()


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    article_data: ArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建文章"""
    article = ArticleService.create_article(
        db,
        article_data,
        current_user.id
    )
    
    # 填充作者信息
    article.author_name = current_user.username
    article.author_full_name = current_user.full_name
    
    return article


@router.get("/", response_model=ArticleListResponse)
async def get_articles(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    category: Optional[str] = Query(None, description="分类"),
    tag: Optional[str] = Query(None, description="标签"),
    author_id: Optional[int] = Query(None, description="作者ID"),
    is_published: Optional[bool] = Query(None, description="是否发布"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取文章列表（支持搜索和筛选）"""
    # 如果未登录或不是作者，只显示已发布的文章
    if current_user is None:
        is_published = True
    elif author_id is None or author_id != current_user.id:
        # 查看他人文章时，只显示已发布的
        is_published = True
    
    skip = (page - 1) * page_size
    articles, total = ArticleService.get_articles(
        db,
        keyword=keyword,
        category=category,
        tag=tag,
        author_id=author_id,
        is_published=is_published,
        skip=skip,
        limit=page_size
    )
    
    items = []
    for article in articles:
        article_dict = ArticleResponse.model_validate(article).model_dump()
        # 列表页不包含附件
        article_dict.pop('attachments', None)
        items.append(ArticleResponse(**article_dict))
    
    return ArticleListResponse(total=total, items=items)


@router.post("/{article_id}/attachments", response_model=ArticleAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def add_attachment(
    article_id: int,
    file_path: str = Query(..., description="文件路径（从上传API获取）"),
    filename: str = Query(..., description="原始文件名"),
    file_size: int = Query(..., description="文件大小"),
    file_type: str = Query(..., description="文件类型"),
    mime_type: str = Query(..., description="MIME类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加文章附件"""
    try:
        article = ArticleService.get_article(db, article_id)
        
        # 权限检查：只有作者可以添加附件
        if article.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有作者可以添加附件"
            )
        
        # 创建附件记录
        attachment = ArticleAttachment(
            article_id=article_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        return ArticleAttachmentResponse.model_validate(attachment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{article_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    article_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文章附件"""
    try:
        article = ArticleService.get_article(db, article_id)
        
        # 权限检查：只有作者可以删除附件
        if article.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有作者可以删除附件"
            )
        
        attachment = db.query(ArticleAttachment).filter(
            ArticleAttachment.id == attachment_id,
            ArticleAttachment.article_id == article_id
        ).first()
        
        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
        
        db.delete(attachment)
        db.commit()
        
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """获取文章详情"""
    try:
        article = ArticleService.get_article(db, article_id)
        
        # 权限检查：未发布文章只有作者可以查看
        if not article.is_published:
            if current_user is None or article.author_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看此文章"
                )
        
        # 增加浏览次数（仅已发布文章）
        if article.is_published:
            article = ArticleService.increment_view_count(db, article_id)
        
        # 填充作者信息
        if article.author:
            article.author_name = article.author.username
            article.author_full_name = article.author.full_name
        
        return article
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文章"""
    try:
        article = ArticleService.update_article(
            db,
            article_id,
            article_data,
            current_user.id
        )
        
        # 填充作者信息
        if article.author:
            article.author_name = article.author.username
            article.author_full_name = article.author.full_name
        
        return article
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文章"""
    try:
        ArticleService.delete_article(db, article_id, current_user.id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/categories/list", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db)
):
    """获取所有分类"""
    categories = ArticleService.get_categories(db)
    return [CategoryResponse(**cat) for cat in categories]


@router.get("/tags/list", response_model=List[TagResponse])
async def get_tags(
    db: Session = Depends(get_db)
):
    """获取所有标签"""
    tags = ArticleService.get_tags(db)
    return [TagResponse(**tag) for tag in tags]


@router.get("/my/articles", response_model=ArticleListResponse)
async def get_my_articles(
    is_published: Optional[bool] = Query(None, description="是否发布"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的文章列表"""
    skip = (page - 1) * page_size
    articles, total = ArticleService.get_articles(
        db,
        author_id=current_user.id,
        is_published=is_published,
        skip=skip,
        limit=page_size
    )
    
    items = []
    for article in articles:
        article_dict = ArticleResponse.model_validate(article).model_dump()
        # 列表页不包含附件
        article_dict.pop('attachments', None)
        items.append(ArticleResponse(**article_dict))
    
    return ArticleListResponse(total=total, items=items)
