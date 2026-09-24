"""
Public Tags Router
GET endpoints for tags
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Tag
from services import TagService
from schemas import TagSchema

router = APIRouter(prefix="/public/tags", tags=["public-tags"])


@router.get("/", response_model=List[TagSchema])
async def list_tags(
    db: AsyncSession = Depends(get_db)
):
    """Get all tags"""
    service = TagService(db)
    
    result = await db.execute(select(Tag))
    tags = result.scalars().all()
    
    return tags


@router.get("/popular", response_model=List[TagSchema])
async def list_popular_tags(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get popular tags (tags used on articles)"""
    service = TagService(db)
    
    from models import ArticleTag
    
    result = await db.execute(
        select(Tag)
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .distinct()
        .limit(limit)
    )
    tags = result.scalars().all()
    
    return tags


@router.get("/{slug}", response_model=TagSchema)
async def get_tag_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tag by slug"""
    service = TagService(db)
    tag = await service.get_by_slug(slug)
    
    if not tag:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return tag
