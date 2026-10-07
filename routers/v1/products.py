"""
FastAPI Router: Products
Path: app/api/v1/products.py
"""
from typing import List, Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db
from routers.deps import get_current_admin
from models.product import Product, ProductCategory
from schemas.product import (
    ProductCreate,
    ProductPublicCard,
    ProductPublicDetail,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(prefix="/api/products", tags=["products"])

class PaginatedProductsResponse(BaseModel):
    items: List[ProductPublicCard]
    total: int
    page: int
    page_size: int
    total_pages: int

@router.get("", response_model=PaginatedProductsResponse)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    category: Optional[ProductCategory] = Query(None, description="Optional category filter"),
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint: Get active digital products with pagination and optional category filter.
    """
    base_query = select(Product).where(Product.is_active == True)
    count_query = select(func.count(Product.id)).where(Product.is_active == True)

    if category:
        base_query = base_query.where(Product.category == category)
        count_query = count_query.where(Product.category == category)

    # Calculate total count
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Query paginated items ordered by newest
    offset = (page - 1) * page_size
    stmt = (
        base_query
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    products = result.scalars().all()

    total_pages = ceil(total / page_size) if total > 0 else 1

    return PaginatedProductsResponse(
        items=[ProductPublicCard.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{slug}", response_model=ProductPublicDetail)
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint: Get full product details by slug.
    """
    stmt = select(Product).where(Product.slug == slug, Product.is_active == True)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found"
        )
    return product

@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin)
):
    """
    Admin only: Create new digital product pattern.
    """
    # Check slug uniqueness
    stmt = select(Product).where(Product.slug == payload.slug)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with slug '{payload.slug}' already exists."
        )

    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@router.put("/{slug}", response_model=ProductRead)
async def update_product(
    slug: str,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin)
):
    """
    Admin only: Update product attributes.
    """
    stmt = select(Product).where(Product.slug == slug)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found"
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "slug" in update_data and update_data["slug"] != slug:
        check_stmt = select(Product).where(Product.slug == update_data["slug"])
        existing_check = await db.execute(check_stmt)
        if existing_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product slug '{update_data['slug']}' is already in use."
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product

@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin)
):
    """
    Admin only: Delete product by slug.
    """
    stmt = select(Product).where(Product.slug == slug)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with slug '{slug}' not found"
        )

    # Preserve order and download history; inactive products disappear from
    # public listings without invalidating past purchases.
    product.is_active = False
    await db.commit()
    return None
