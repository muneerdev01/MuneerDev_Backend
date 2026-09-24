"""
Pydantic Schemas for MediaAsset Model
"""
from typing import Optional

from pydantic import BaseModel, Field


class MediaAssetBase(BaseModel):
    """Base media asset schema with common fields"""
    file_name: str = Field(..., min_length=1, max_length=255)
    original_name: str = Field(..., min_length=1, max_length=500)
    url: str = Field(..., min_length=1, max_length=1000)
    mime_type: str = Field(..., min_length=1, max_length=100)
    size_bytes: int = Field(..., ge=0)
    alt_text: Optional[str] = Field(default=None, max_length=500)
    caption: Optional[str] = Field(default=None, max_length=1000)


class MediaAssetCreate(MediaAssetBase):
    """Schema for creating a new media asset"""
    pass


class MediaAssetUpdate(MediaAssetBase):
    """Schema for updating a media asset"""
    url: Optional[str] = Field(default=None, min_length=1, max_length=1000)


class MediaAssetOut(MediaAssetBase):
    """Schema for media asset response"""
    id: str
    created_at: str

    class Config:
        from_attributes = True
