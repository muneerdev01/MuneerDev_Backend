"""
Media Upload Router
Upload images to storage and save metadata in database
"""
import os
import uuid
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import MediaAsset, Article
from models.enums import EntityTypeEnum
from services import MediaAssetService, ArticleService
from security.rbac import require_any_role
from storage import storage_service, StorageService
from events import AuditLogger

router = APIRouter(prefix="/admin/media", tags=["media"])


@router.post("/upload", response_model=dict)
async def upload_media(
    file: UploadFile = File(...),
    alt_text: Optional[str] = None,
    caption: Optional[str] = None,
    user: dict = Depends(require_any_role(["ADMIN", "EDITOR", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(lambda: storage_service)
):
    """
    Upload media file to storage.
    Supports images and other file types.
    """
    # Validate file type
    allowed_types = [
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
        "image/svg+xml",
        "application/pdf",
        "video/mp4", "video/webm"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".bin"
    safe_filename = f"{secrets.token_hex(8)}{file_extension}"
    
    # Create storage path
    bucket = os.getenv("STORAGE_BUCKET", "media")
    upload_path = f"articles/{datetime.utcnow().strftime('%Y/%m/%d')}/{safe_filename}"
    
    try:
        # Upload to storage
        storage_result = await storage.upload_file(
            file=file.file,
            bucket=bucket,
            file_path=upload_path,
            metadata={
                "content-type": file.content_type,
                "uploaded_by": user.get("email", "unknown")
            }
        )
        
        # Create media asset record
        media_asset = MediaAsset(
            file_name=upload_path,
            original_name=file.filename or "unknown",
            url=storage_result.get("url", f"/storage/{bucket}/{upload_path}"),
            mime_type=file.content_type,
            size_bytes=storage_result.get("size", 0),
            alt_text=alt_text or "",
            caption=caption or ""
        )
        
        db.add(media_asset)
        await db.commit()
        await db.refresh(media_asset)
        
        # Log audit event
        audit_logger = AuditLogger(db)
        await audit_logger.log_create(
            entity_type=EntityTypeEnum.article,
            entity_id=str(media_asset.id),
            user_email=user.get("email", "unknown"),
            entity_name=file.filename or "unknown",
            details={
                "mime_type": file.content_type,
                "size_bytes": media_asset.size_bytes
            }
        )
        
        return {
            "message": "File uploaded successfully",
            "media_asset": {
                "id": str(media_asset.id),
                "file_name": media_asset.file_name,
                "original_name": media_asset.original_name,
                "url": media_asset.url,
                "mime_type": media_asset.mime_type,
                "size_bytes": media_asset.size_bytes,
                "alt_text": media_asset.alt_text,
                "caption": media_asset.caption
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: str,
    user: dict = Depends(require_any_role(["ADMIN", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(lambda: storage_service)
):
    """Delete a media asset"""
    service = MediaAssetService(db)
    media_asset = await service.get_by_id(media_id)
    
    if not media_asset:
        raise HTTPException(status_code=404, detail="Media asset not found")
    
    # Get bucket and path
    bucket = os.getenv("STORAGE_BUCKET", "media")
    file_path = media_asset.file_name
    
    try:
        # Delete from storage
        await storage.delete_file(bucket, file_path)
        
        # Delete from database
        await service.delete(media_id)
        
        # Log audit event
        audit_logger = AuditLogger(db)
        await audit_logger.log_delete(
            entity_type=EntityTypeEnum.article,
            entity_id=str(media_asset.id),
            user_email=user.get("email", "unknown"),
            entity_name=media_asset.original_name
        )
        
        return None
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("/{media_id}", response_model=dict)
async def get_media(
    media_id: str,
    user: dict = Depends(require_any_role(["ADMIN", "EDITOR", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """Get media asset details"""
    service = MediaAssetService(db)
    media_asset = await service.get_by_id(media_id)
    
    if not media_asset:
        raise HTTPException(status_code=404, detail="Media asset not found")
    
    return {
        "id": str(media_asset.id),
        "file_name": media_asset.file_name,
        "original_name": media_asset.original_name,
        "url": media_asset.url,
        "mime_type": media_asset.mime_type,
        "size_bytes": media_asset.size_bytes,
        "alt_text": media_asset.alt_text,
        "caption": media_asset.caption,
        "created_at": media_asset.created_at
    }


@router.get("/", response_model=list)
async def list_media(
    skip: int = 0,
    limit: int = 20,
    user: dict = Depends(require_any_role(["ADMIN", "EDITOR", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """List media assets"""
    service = MediaAssetService(db)
    media_assets = await service.get_all(skip=skip, limit=limit)
    
    return [
        {
            "id": str(m.id),
            "file_name": m.file_name,
            "original_name": m.original_name,
            "url": m.url,
            "mime_type": m.mime_type,
            "size_bytes": m.size_bytes,
            "alt_text": m.alt_text,
            "created_at": m.created_at
        }
        for m in media_assets
    ]
