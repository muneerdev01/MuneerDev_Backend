"""
Tags Router
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Tag, Article
from schemas import TagSchema, TagListSchema
from services import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=TagListSchema)
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all tags"""
    service = TagService(db)
    
    result = await db.execute(select(Tag).offset(skip).limit(limit))
    tags = result.scalars().all()
    
    total = len(tags)
    return {"items": tags, "total": total, "page": 1, "page_size": limit}


@router.get("/{tag_id}", response_model=TagSchema)
async def get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tag by ID"""
    service = TagService(db)
    tag = await service.get_by_id(tag_id)
    
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    
    return tag


@router.get("/slug/{slug}", response_model=TagSchema)
async def get_tag_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tag by slug"""
    service = TagService(db)
    tag = await service.get_by_slug(slug)
    
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    
    return tag


@router.post("/", response_model=TagSchema, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: TagSchema,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tag"""
    service = TagService(db)
    
    # Convert schema to dict for service
    data = tag.model_dump(exclude_unset=True)
    
    db_tag = await service.create_with_slug(data)
    return db_tag


@router.put("/{tag_id}", response_model=TagSchema)
async def update_tag(
    tag_id: str,
    tag: TagSchema,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing tag"""
    service = TagService(db)
    db_tag = await service.get_by_id(tag_id)
    
    if not db_tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    
    # Convert schema to dict for service
    data = tag.model_dump(exclude_unset=True)
    
    db_tag = await service.update_with_slug(tag_id, data)
    return db_tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a tag"""
    service = TagService(db)
    tag = await service.get_by_id(tag_id)
    
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    
    # Check if tag is associated with articles
    result = await db.execute(select(Article).join(Article.tags).where(Tag.id == tag_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete tag associated with articles"
        )
    
    await service.delete(tag_id)
    return None


@router.get("/{tag_id}/articles")
async def get_tag_articles(
    tag_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all articles associated with a tag"""
    service = TagService(db)
    tag = await service.get_by_id(tag_id)
    
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    
    articles = await service.get_article_tags(tag_id)
    return {"articles": articles, "total": len(articles)}
