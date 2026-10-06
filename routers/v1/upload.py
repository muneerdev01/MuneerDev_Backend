"""
FastAPI Router: Supabase Storage Multipart Upload
Path: app/api/v1/upload.py
"""
import uuid
from typing import Literal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from supabase import Client

from app.api.deps import get_current_admin, get_supabase_client

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Constraints
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_PRODUCT_EXTENSIONS = {"pdf", "zip"}

class UploadResponse(BaseModel):
    file_path: str
    file_size: int
    content_type: str
    bucket: str
    public_url: str | None = None

@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    file_type: Literal["image", "product_file"] = Form(...),
    _admin: dict = Depends(get_current_admin),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Admin only multipart upload:
    - Images (png/jpg/webp) -> Public bucket 'projects'
    - Product files (pdf/zip max 100MB) -> Private bucket 'products'
    """
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # Validate file extensions & determine bucket
    if file_type == "image":
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format '.{ext}'. Allowed: {ALLOWED_IMAGE_EXTENSIONS}"
            )
        bucket_name = "projects"
        storage_path = f"images/{uuid.uuid4().hex}_{filename}"
    elif file_type == "product_file":
        if ext not in ALLOWED_PRODUCT_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid digital product format '.{ext}'. Only PDF and ZIP allowed."
            )
        bucket_name = "products"
        storage_path = f"patterns/{uuid.uuid4().hex}_{filename}"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_type must be either 'image' or 'product_file'"
        )

    # Read content and enforce 100MB size limit
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed limit of 100MB (actual: {file_size / (1024*1024):.2f}MB)"
        )

    content_type = file.content_type or "application/octet-stream"

    try:
        # Upload buffer to Supabase Storage
        response = supabase.storage.from_(bucket_name).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type, "upsert": "false"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase Storage upload error: {str(e)}"
        )

    # Compute public URL for public bucket images
    public_url = None
    if bucket_name == "projects":
        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)

    return UploadResponse(
        file_path=storage_path,
        file_size=file_size,
        content_type=content_type,
        bucket=bucket_name,
        public_url=public_url
    )
