"""
Pydantic Schemas for Article Model
"""
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ArticleBase(BaseModel):
    """Base article schema with common fields"""
    slug: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    excerpt: str = Field(..., min_length=1, max_length=1000)
    content: str
    content_format: str = Field(..., pattern="^(markdown|html|rich_text)$")
    blog_type: str = Field(..., pattern="^(TECH|HEALTHCARE)$")
    category_id: Optional[str] = None
    status: str = Field(default="DRAFT", pattern="^(DRAFT|PUBLISHED|ARCHIVED)$")
    reading_time: int = Field(default=0, ge=0)
    featured: bool = Field(default=False)
    featured_image: Optional[str] = None
    image_alt_text: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    og_image: Optional[str] = None


class ArticleCreate(ArticleBase):
    """Schema for creating a new article"""
    pass


class ArticleUpdate(ArticleBase):
    """Schema for updating an article"""
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)


class ArticleAuthor(BaseModel):
    """Author information"""
    name: str = Field(default="")
    email: str = Field(default="")


class ArticleOut(ArticleBase):
    """Schema for article response"""
    id: str
    author: Dict[str, Any]
    table_of_contents: List[Any]
    references: List[Any]
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True
