"""
Pydantic v2 Schemas: Product
Path: app/schemas/product.py
"""
import re
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.product import ProductCategory

class ProductBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, example="Nordic Cable Knit Sweater Pattern")
    slug: str = Field(..., min_length=3, max_length=250, example="nordic-cable-knit-sweater-pattern")
    description: str = Field(..., min_length=20, example="Includes PDF pattern in sizes XS to 3XL with video stitch tutorials.")
    price: Decimal = Field(..., ge=Decimal("0.50"), decimal_places=2, example=8.50)
    category: ProductCategory = Field(..., example=ProductCategory.PATTERNS)
    preview_images: List[str] = Field(default_factory=list, example=["https://bucket.supabase.co/storage/v1/object/public/previews/sweater-1.webp"])
    file_path: str = Field(..., min_length=5, example="products/patterns/cable_knit_v2.pdf")
    file_size: int = Field(..., gt=0, example=4821500)  # Size in bytes
    is_active: bool = Field(default=True)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", cleaned):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens (e.g. 'cable-knit-pattern')")
        return cleaned

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Price must be greater than 0.00")
        return round(v, 2)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    slug: Optional[str] = Field(None, min_length=3, max_length=250)
    description: Optional[str] = Field(None, min_length=20)
    price: Optional[Decimal] = Field(None, ge=Decimal("0.50"), decimal_places=2)
    category: Optional[ProductCategory] = None
    preview_images: Optional[List[str]] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None

class ProductRead(ProductBase):
    id: int
    sales_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductPublicCard(BaseModel):
    """Optimized lightweight schema for the public Etsy-style grid cards."""
    id: int
    title: str
    slug: str
    price: Decimal
    category: ProductCategory
    preview_images: List[str]
    sales_count: int

    model_config = ConfigDict(from_attributes=True)
