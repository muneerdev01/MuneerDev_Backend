"""
FastAPI Router: Expiring Digital Download Delivery
Path: app/api/v1/download.py
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from supabase import Client

from database.config import get_db
from routers.deps import get_supabase_client
from models.download_token import DownloadToken
from models.order import Order, OrderStatus
from models.product import Product

router = APIRouter(prefix="/api/download", tags=["download"])

@router.get("/{token}")
async def download_pattern_by_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Public token delivery endpoint:
    1. Validates UUID format
    2. Verifies token existence and joins Order + Product
    3. Verifies Order status is PAID
    4. Checks that current UTC time < token.expires_at
    5. Requests 1-hour (3600s) signed URL from Supabase Storage private bucket
    6. Issues a 307 Temporary Redirect to the signed URL
    """
    # 1. Validate UUID syntax
    try:
        token_uuid = uuid.UUID(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token format. Must be a valid UUID."
        )

    # 2. Query token with joined order and product
    stmt = (
        select(DownloadToken)
        .options(
            selectinload(DownloadToken.order).selectinload(Order.product)
        )
        .where(DownloadToken.token == token_uuid)
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download link not found. Please verify the URL or contact support."
        )

    # 3. Check Order status
    order: Order = token_record.order
    if not order or order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Order has not been completed or verified."
        )

    # 4. Check token expiration
    now = datetime.now(timezone.utc)
    target_expiry = (
        token_record.expires_at 
        if token_record.expires_at.tzinfo 
        else token_record.expires_at.replace(tzinfo=timezone.utc)
    )

    if now >= target_expiry:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This download link expired after 24 hours. Check your email or contact support to request a new link."
        )

    # 5. Fetch private storage path from product
    product: Product = order.product
    if not product or not product.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product digital file is not configured on the server."
        )

    # 6. Generate 1-hour signed URL from private 'products' bucket
    try:
        signed_url_res = supabase.storage.from_("products").create_signed_url(
            path=product.file_path,
            expires_in=3600  # 1 hour
        )
        signed_url = signed_url_res.get("signedURL") or signed_url_res.get("signedUrl")
        if not signed_url:
            raise ValueError("No signed URL in Supabase response")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate secure download link.",
        ) from e

    # 7. Redirect buyer directly to download stream
    return RedirectResponse(
        url=signed_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Cache-Control": "no-store"},
    )
