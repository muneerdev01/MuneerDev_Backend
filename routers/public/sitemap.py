"""
Sitemap Data Router
Lightweight endpoint for Next.js dynamic sitemap generation
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Article, Category, Tag
from models.enums import ArticleStatusEnum, BlogTypeEnum

router = APIRouter(prefix="/public/sitemap", tags=["public-sitemap"])


class SitemapItem(BaseModel):
    """Sitemap item structure"""
    slug: str
    updated_at: Optional[str] = None
    blog_type: Optional[str] = None
    changefreq: str = "monthly"
    priority: float = 0.5


class SitemapData(BaseModel):
    """Sitemap response structure"""
    articles: List[SitemapItem]
    categories: List[SitemapItem]
    tags: List[SitemapItem]
    last_build_date: str


@router.get("/data", response_model=SitemapData)
async def get_sitemap_data(
    db: AsyncSession = Depends(get_db)
):
    """
    Get sitemap data for Next.js dynamic sitemap.
    Returns only slugs and timestamps for dynamic sitemap generation.
    """
    # Get published articles
    result = await db.execute(
        select(Article).where(Article.status == ArticleStatusEnum.PUBLISHED.value)
    )
    articles = result.scalars().all()
    
    article_items = [
        SitemapItem(
            slug=article.slug,
            updated_at=article.updated_at.isoformat() if article.updated_at else None,
            blog_type=article.blog_type,
            changefreq="weekly",
            priority=0.8
        )
        for article in articles
    ]
    
    # Get categories
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    
    category_items = [
        SitemapItem(
            slug=category.slug,
            updated_at=category.updated_at.isoformat() if category.updated_at else None,
            blog_type=category.blog_type,
            changefreq="monthly",
            priority=0.5
        )
        for category in categories
    ]
    
    # Get tags
    result = await db.execute(select(Tag))
    tags = result.scalars().all()
    
    tag_items = [
        SitemapItem(
            slug=tag.slug,
            updated_at=tag.updated_at.isoformat() if tag.updated_at else None,
            changefreq="monthly",
            priority=0.4
        )
        for tag in tags
    ]
    
    return SitemapData(
        articles=article_items,
        categories=category_items,
        tags=tag_items,
        last_build_date=datetime.utcnow().isoformat()
    )


@router.get("/articles", response_model=List[SitemapItem])
async def get_article_sitemap(
    db: AsyncSession = Depends(get_db)
):
    """Get sitemap data for articles only"""
    result = await db.execute(
        select(Article).where(Article.status == ArticleStatusEnum.PUBLISHED.value)
    )
    articles = result.scalars().all()
    
    return [
        SitemapItem(
            slug=article.slug,
            updated_at=article.updated_at.isoformat() if article.updated_at else None,
            blog_type=article.blog_type,
            changefreq="weekly",
            priority=0.8
        )
        for article in articles
    ]


@router.get("/categories", response_model=List[SitemapItem])
async def get_category_sitemap(
    db: AsyncSession = Depends(get_db)
):
    """Get sitemap data for categories only"""
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    
    return [
        SitemapItem(
            slug=category.slug,
            updated_at=category.updated_at.isoformat() if category.updated_at else None,
            blog_type=category.blog_type,
            changefreq="monthly",
            priority=0.5
        )
        for category in categories
    ]


@router.get("/tags", response_model=List[SitemapItem])
async def get_tag_sitemap(
    db: AsyncSession = Depends(get_db)
):
    """Get sitemap data for tags only"""
    result = await db.execute(select(Tag))
    tags = result.scalars().all()
    
    return [
        SitemapItem(
            slug=tag.slug,
            updated_at=tag.updated_at.isoformat() if tag.updated_at else None,
            changefreq="monthly",
            priority=0.4
        )
        for tag in tags
    ]
