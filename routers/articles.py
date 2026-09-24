"""
Articles Router
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Article, Category, Tag, ArticleTag
from models.enums import BlogTypeEnum, ArticleStatusEnum
from schemas import ArticleSchema, ArticleListSchema
from services import ArticleService

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=ArticleListSchema)
async def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    blog_type: BlogTypeEnum = Query(None),
    category_id: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all published articles"""
    service = ArticleService(db)
    
    articles = await service.list_published(
        skip=skip,
        limit=limit,
        blog_type=blog_type,
        category_id=category_id
    )
    
    total = len(articles)
    return {"items": articles, "total": total, "page": 1, "page_size": limit}


@router.get("/{article_id}", response_model=ArticleSchema)
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific published article by ID"""
    service = ArticleService(db)
    article = await service.get_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    if article.status != ArticleStatusEnum.PUBLISHED.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not published")
    
    return await service.format_for_response(article)


@router.get("/slug/{slug}", response_model=ArticleSchema)
async def get_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific published article by slug"""
    service = ArticleService(db)
    article = await service.get_published_by_slug(slug)
    
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    return await service.format_for_response(article)


@router.post("/", response_model=ArticleSchema, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleSchema,
    db: AsyncSession = Depends(get_db)
):
    """Create a new article"""
    service = ArticleService(db)
    
    # Verify category exists
    result = await db.execute(select(Category).where(Category.id == article.category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category_id")
    
    # Convert schema to dict for service
    data = article.model_dump(exclude_unset=True)
    
    db_article = await service.create_with_business_logic(data)
    return await service.format_for_response(db_article)


@router.put("/{article_id}", response_model=ArticleSchema)
async def update_article(
    article_id: str,
    article: ArticleSchema,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing article"""
    service = ArticleService(db)
    db_article = await service.get_by_id(article_id)
    
    if not db_article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    # Verify category exists
    result = await db.execute(select(Category).where(Category.id == article.category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category_id")
    
    # Convert schema to dict for service
    data = article.model_dump(exclude_unset=True)
    
    db_article = await service.update_with_business_logic(article_id, data)
    return await service.format_for_response(db_article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an article"""
    service = ArticleService(db)
    article = await service.get_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    await service.delete(article_id)
    return None


@router.post("/{article_id}/tags/{tag_id}", status_code=status.HTTP_201_CREATED)
async def add_tag_to_article(
    article_id: str,
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Add a tag to an article"""
    service = ArticleService(db)
    
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    if await service.add_tag(article_id, tag_id):
        return {"message": "Tag added successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag already associated with article"
        )


@router.delete("/{article_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_article(
    article_id: str,
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a tag from an article"""
    service = ArticleService(db)
    
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    if await service.remove_tag(article_id, tag_id):
        return None
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not associated with article"
        )


@router.put("/{article_id}/publish")
async def publish_article(
    article_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Publish an article"""
    service = ArticleService(db)
    article = await service.get_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    
    db_article = await service.publish_article(article_id)
    return await service.format_for_response(db_article)
