"""
Public Categories Router
GET endpoints for categories
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Category
from models.enums import BlogTypeEnum
from services import CategoryService
from schemas import CategorySchema

router = APIRouter(prefix="/public/categories", tags=["public-categories"])


@router.get("/", response_model=List[CategorySchema])
async def list_categories(
    blog_type: Optional[BlogTypeEnum] = Query(None, description="Filter by blog type"),
    db: AsyncSession = Depends(get_db)
):
    """Get all categories with optional blog type filter"""
    service = CategoryService(db)
    
    if blog_type:
        categories = await service.list_by_blog_type(blog_type)
    else:
        result = await db.execute(select(Category))
        categories = result.scalars().all()
    
    return categories


@router.get("/blog/{blog_type}", response_model=List[CategorySchema])
async def list_categories_by_blog_type(
    blog_type: BlogTypeEnum,
    db: AsyncSession = Depends(get_db)
):
    """Get categories by blog type"""
    service = CategoryService(db)
    categories = await service.list_by_blog_type(blog_type)
    return categories


@router.get("/{slug}", response_model=CategorySchema)
async def get_category_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by slug"""
    service = CategoryService(db)
    category = await service.get_by_slug(slug)
    
    if not category:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category
