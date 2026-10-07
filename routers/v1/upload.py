"""
FastAPI Router: Supabase Storage Multipart Upload
Path: app/api/v1/upload.py
"""
import uuid
from typing import Literal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from supabase import Client

from utils.upload_validation import MAX_UPLOAD_BYTES, validate_upload
from routers.deps import get_current_admin, get_supabase_client

router = APIRouter(prefix="/api/upload", tags=["upload"])

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
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    content_type = validate_upload(file.filename, file.content_type, content, file_type)
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    bucket_name = "projects" if file_type == "image" else "products"
    directory = "images" if file_type == "image" else "patterns"
    storage_path = f"{directory}/{uuid.uuid4().hex}.{ext}"

    try:
        # Upload buffer to Supabase Storage
        supabase.storage.from_(bucket_name).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type, "upsert": "false"}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase Storage upload failed.",
        ) from exc

    # Compute public URL for public bucket images
    public_url = None
    if bucket_name == "projects":
        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)

    return UploadResponse(
        file_path=storage_path,
        file_size=len(content),
        content_type=content_type,
        bucket=bucket_name,
        public_url=public_url
    )
