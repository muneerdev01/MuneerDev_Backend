"""
Categories Router
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Category, Article
from models.enums import BlogTypeEnum
from schemas import CategorySchema, CategoryListSchema
from services import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=CategoryListSchema)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    blog_type: BlogTypeEnum = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all categories with optional blog type filter"""
    service = CategoryService(db)
    
    if blog_type:
        categories = await service.list_by_blog_type(blog_type)
    else:
        result = await db.execute(select(Category).offset(skip).limit(limit))
        categories = result.scalars().all()
    
    total = len(categories)
    return {"items": categories, "total": total, "page": 1, "page_size": limit}


@router.get("/{category_id}", response_model=CategorySchema)
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by ID"""
    service = CategoryService(db)
    category = await service.get_by_id(category_id)
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    return category


@router.get("/slug/{slug}", response_model=CategorySchema)
async def get_category_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by slug"""
    service = CategoryService(db)
    category = await service.get_by_slug(slug)
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    return category


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategorySchema,
    db: AsyncSession = Depends(get_db)
):
    """Create a new category"""
    service = CategoryService(db)
    
    # Convert schema to dict for service
    data = category.model_dump(exclude_unset=True)
    
    db_category = await service.create_with_slug(data)
    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: str,
    category: CategorySchema,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing category"""
    service = CategoryService(db)
    db_category = await service.get_by_id(category_id)
    
    if not db_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Convert schema to dict for service
    data = category.model_dump(exclude_unset=True)
    
    db_category = await service.update_with_slug(category_id, data)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a category"""
    service = CategoryService(db)
    category = await service.get_by_id(category_id)
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Check if category has articles
    result = await db.execute(select(Article).where(Article.category_id == category_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing articles"
        )
    
    await service.delete(category_id)
    return None
