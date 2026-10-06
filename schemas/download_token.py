"""
Pydantic v2 Schemas: DownloadToken
Path: app/schemas/download_token.py
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class DownloadTokenRead(BaseModel):
    id: int
    order_id: int
    token: uuid.UUID
    expires_at: datetime
    is_expired: bool

    model_config = ConfigDict(from_attributes=True)

class DownloadTokenVerifyResponse(BaseModel):
    """Returned to /download/[token] frontend page upon token verification."""
    token: uuid.UUID
    product_title: str
    product_category: str
    file_size_bytes: int
    expires_at: datetime
    is_valid: bool
    download_url: str = Field(..., description="1-hour Supabase Storage signed download URL")
