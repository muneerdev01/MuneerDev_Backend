"""
Pydantic Schemas for Category Model
"""
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base category schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    blog_type: str = Field(..., pattern="^(TECH|HEALTHCARE)$")
    entity_type: str = Field(..., pattern="^(article|project|service|resource|product|customer|lead)$")
    description: Optional[str] = Field(default=None, max_length=1000)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    pass


class CategoryUpdate(CategoryBase):
    """Schema for updating a category"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)


class CategoryOut(CategoryBase):
    """Schema for category response"""
    id: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
