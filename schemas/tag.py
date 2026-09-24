"""
Tag Schema Definitions
"""
from typing import List

from pydantic import BaseModel, Field


class TagSchema(BaseModel):
    """Tag schema with all fields"""
    id: str
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    created_at: str

    class Config:
        from_attributes = True


class TagListSchema(BaseModel):
    """Tag list response schema"""
    items: List[TagSchema]
    total: int
    page: int = 1
    page_size: int = 10
