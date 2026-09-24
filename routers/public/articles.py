"""
Public Articles Router
GET endpoints for published articles with filters
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Article, Category, Tag, ArticleTag
from models.enums import ArticleStatusEnum, BlogTypeEnum
from services import ArticleService
from schemas import ArticleSchema

router = APIRouter(prefix="/public/articles", tags=["public-articles"])


@router.get("/", response_model=List[ArticleSchema])
async def list_articles(
    blog_type: Optional[BlogTypeEnum] = Query(None, description="Filter by blog type"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    tag: Optional[str] = Query(None, description="Filter by tag slug"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of published articles with optional filters.
    """
    service = ArticleService(db)
    
    # Start with published articles
    query = select(Article).where(Article.status == ArticleStatusEnum.PUBLISHED.value)
    
    # Apply filters
    if blog_type:
        query = query.where(Article.blog_type == blog_type)
    
    if category:
        query = query.join(Category).where(Category.slug == category)
    
    if tag:
        query = query.join(ArticleTag).join(Tag).where(Tag.slug == tag)
    
    if search:
        query = query.where(
            (Article.title.ilike(f"%{search}%")) |
            (Article.content.ilike(f"%{search}%"))
        )
    
    # Get total count
    count_query = query.with_only_columns([Article.id]).order_by(None)
    result = await db.execute(count_query)
    total_items = len(result.scalars().all())
    
    # Calculate pagination
    total_pages = (total_items + page_size - 1) // page_size
    offset = (page - 1) * page_size
    
    # Get paginated results
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return [
        await service.format_for_response(article)
        for article in articles
    ]


@router.get("/featured", response_model=List[ArticleSchema])
async def list_featured_articles(
    blog_type: Optional[BlogTypeEnum] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get featured published articles"""
    service = ArticleService(db)
    
    query = select(Article).where(
        Article.status == ArticleStatusEnum.PUBLISHED.value,
        Article.featured == True
    )
    
    if blog_type:
        query = query.where(Article.blog_type == blog_type)
    
    query = query.order_by(Article.published_at.desc())
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return [
        await service.format_for_response(article)
        for article in articles[:4]  # Limit to 4 featured articles
    ]


@router.get("/recent", response_model=List[ArticleSchema])
async def list_recent_articles(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Get recent published articles"""
    service = ArticleService(db)
    
    query = select(Article).where(
        Article.status == ArticleStatusEnum.PUBLISHED.value
    ).order_by(Article.published_at.desc()).limit(limit)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return [
        await service.format_for_response(article)
        for article in articles
    ]


@router.get("/{slug}", response_model=ArticleSchema)
async def get_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific published article by slug"""
    service = ArticleService(db)
    article = await service.get_published_by_slug(slug)
    
    if not article:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Article not found")
    
    return await service.format_for_response(article)
