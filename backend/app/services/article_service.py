"""知识分享服务"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Tuple, Optional
from datetime import datetime

from app.models.article import Article
from app.models.article_attachment import ArticleAttachment
from app.models.user import User
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.schemas.article import ArticleCreate, ArticleUpdate


class ArticleService:
    """文章服务类"""

    @staticmethod
    def create_article(
        db: Session,
        article_data: ArticleCreate,
        author_id: int
    ) -> Article:
        """创建文章"""
        article = Article(
            title=article_data.title,
            content=article_data.content,
            category=article_data.category,
            tags=article_data.tags,
            is_published=article_data.is_published,
            author_id=author_id,
            view_count=0
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        return article

    @staticmethod
    def get_article(db: Session, article_id: int) -> Article:
        """获取文章详情"""
        article = db.query(Article).options(
            joinedload(Article.author),
            joinedload(Article.attachments)
        ).filter(Article.id == article_id).first()
        if not article:
            raise NotFoundError("文章", str(article_id))
        return article

    @staticmethod
    def update_article(
        db: Session,
        article_id: int,
        article_data: ArticleUpdate,
        user_id: int
    ) -> Article:
        """更新文章"""
        article = ArticleService.get_article(db, article_id)
        
        # 权限检查：只有作者可以修改
        if article.author_id != user_id:
            raise PermissionDeniedError("只有作者可以修改文章")
        
        # 更新字段
        if article_data.title is not None:
            article.title = article_data.title
        if article_data.content is not None:
            article.content = article_data.content
        if article_data.category is not None:
            article.category = article_data.category
        if article_data.tags is not None:
            article.tags = article_data.tags
        if article_data.is_published is not None:
            article.is_published = article_data.is_published
        
        article.updated_at = datetime.now()
        db.commit()
        db.refresh(article)
        return article

    @staticmethod
    def delete_article(
        db: Session,
        article_id: int,
        user_id: int
    ) -> None:
        """删除文章"""
        article = ArticleService.get_article(db, article_id)
        
        # 权限检查：只有作者可以删除
        if article.author_id != user_id:
            raise PermissionDeniedError("只有作者可以删除文章")
        
        db.delete(article)
        db.commit()

    @staticmethod
    def get_articles(
        db: Session,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        author_id: Optional[int] = None,
        is_published: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Article], int]:
        """获取文章列表（支持搜索和筛选）"""
        query = db.query(Article)
        
        # 关键词搜索（标题和内容）
        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Article.title.like(keyword_pattern),
                    Article.content.like(keyword_pattern)
                )
            )
        
        # 分类筛选
        if category:
            query = query.filter(Article.category == category)
        
        # 标签筛选
        if tag:
            # tags字段可能是逗号分隔的字符串，使用LIKE查询
            tag_pattern = f"%{tag}%"
            query = query.filter(Article.tags.like(tag_pattern))
        
        # 作者筛选
        if author_id:
            query = query.filter(Article.author_id == author_id)
        
        # 发布状态筛选
        if is_published is not None:
            query = query.filter(Article.is_published == is_published)
        
        # 总数
        total = query.count()
        
        # 分页查询（按创建时间倒序）
        articles = query.options(
            joinedload(Article.author)
        ).order_by(Article.created_at.desc()).offset(skip).limit(limit).all()
        
        # 填充作者信息
        for article in articles:
            if article.author:
                article.author_name = article.author.username
                article.author_full_name = article.author.full_name
        
        return articles, total

    @staticmethod
    def increment_view_count(db: Session, article_id: int) -> Article:
        """增加文章浏览次数"""
        article = ArticleService.get_article(db, article_id)
        article.view_count += 1
        db.commit()
        db.refresh(article)
        return article

    @staticmethod
    def get_categories(db: Session) -> List[dict]:
        """获取所有分类及其文章数量"""
        categories = db.query(
            Article.category,
            func.count(Article.id).label('count')
        ).filter(
            Article.category.isnot(None),
            Article.category != '',
            Article.is_published == True
        ).group_by(Article.category).all()
        
        return [
            {"name": cat[0], "count": cat[1]}
            for cat in categories
        ]

    @staticmethod
    def get_tags(db: Session) -> List[dict]:
        """获取所有标签及其文章数量"""
        # 获取所有已发布文章的所有标签
        articles = db.query(Article.tags).filter(
            Article.tags.isnot(None),
            Article.tags != '',
            Article.is_published == True
        ).all()
        
        # 统计标签
        tag_count = {}
        for article in articles:
            if article.tags:
                tags = [tag.strip() for tag in article.tags.split(',') if tag.strip()]
                for tag in tags:
                    tag_count[tag] = tag_count.get(tag, 0) + 1
        
        return [
            {"name": tag, "count": count}
            for tag, count in sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        ]

    @staticmethod
    def get_user_articles(
        db: Session,
        user_id: int,
        is_published: Optional[bool] = None
    ) -> List[Article]:
        """获取用户的所有文章"""
        query = db.query(Article).filter(Article.author_id == user_id)
        
        if is_published is not None:
            query = query.filter(Article.is_published == is_published)
        
        return query.order_by(Article.created_at.desc()).all()
