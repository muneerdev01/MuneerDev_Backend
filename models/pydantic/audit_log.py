"""
Pydantic Schemas for AuditLog Model
"""
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class AuditLogBase(BaseModel):
    """Base audit log schema with common fields"""
    action: str = Field(..., min_length=1, max_length=100)
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: str
    user_email: str = Field(..., min_length=1, max_length=255)
    details: Optional[Dict[str, Any]] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating a new audit log"""
    pass


class AuditLogOut(AuditLogBase):
    """Schema for audit log response"""
    id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
