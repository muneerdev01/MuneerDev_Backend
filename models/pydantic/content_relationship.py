"""
Pydantic Schemas for ContentRelationship Model
"""
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class ContentRelationshipBase(BaseModel):
    """Base content relationship schema with common fields"""
    source_type: str = Field(..., pattern="^(article|project|service|resource|product|customer|lead)$")
    source_id: str
    target_type: str = Field(..., pattern="^(article|project|service|resource|product|customer|lead)$")
    target_id: str
    relationship_type: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(default=0, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class ContentRelationshipCreate(ContentRelationshipBase):
    """Schema for creating a new content relationship"""
    pass


class ContentRelationshipUpdate(ContentRelationshipBase):
    """Schema for updating a content relationship"""
    display_order: Optional[int] = Field(default=None, ge=0)


class ContentRelationshipOut(ContentRelationshipBase):
    """Schema for content relationship response"""
    id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
