"""
Category Schema Definitions
"""
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class CategorySchema(BaseModel):
    """Category schema with all fields"""
    id: str
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    blog_type: str = Field(..., pattern="^(TECH|HEALTHCARE)$")
    entity_type: str = Field(..., pattern="^(article|project|service|resource|product|customer|lead)$")
    description: Optional[str] = Field(default=None, max_length=1000)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CategoryListSchema(BaseModel):
    """Category list response schema"""
    items: List[CategorySchema]
    total: int
    page: int = 1
    page_size: int = 10
