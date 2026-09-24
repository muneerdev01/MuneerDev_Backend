"""
Article Schema Definitions
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ArticleSchema(BaseModel):
    """Article schema with all fields"""
    id: str
    slug: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    excerpt: str = Field(..., min_length=1, max_length=1000)
    content: str
    content_format: str = Field(..., pattern="^(markdown|html|rich_text)$")
    blog_type: str = Field(..., pattern="^(TECH|HEALTHCARE)$")
    category_id: str
    status: str = Field(default="DRAFT", pattern="^(DRAFT|PUBLISHED|ARCHIVED)$")
    reading_time: int = Field(default=0, ge=0)
    featured: bool = Field(default=False)
    featured_image: Optional[str] = None
    image_alt_text: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    og_image: Optional[str] = None
    author: Dict[str, Any] = Field(default_factory=lambda: {"name": "", "email": ""})
    table_of_contents: List[Any] = Field(default_factory=list)
    references: List[Any] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


class ArticleListSchema(BaseModel):
    """Article list response schema"""
    items: List[ArticleSchema]
    total: int
    page: int = 1
    page_size: int = 10
