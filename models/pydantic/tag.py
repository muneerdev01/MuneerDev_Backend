"""
Pydantic Schemas for Tag Model
"""
from typing import Optional

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Base tag schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)


class TagCreate(TagBase):
    """Schema for creating a new tag"""
    pass


class TagUpdate(TagBase):
    """Schema for updating a tag"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=100)


class TagOut(TagBase):
    """Schema for tag response"""
    id: str
    created_at: str

    class Config:
        from_attributes = True
