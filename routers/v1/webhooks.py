"""
FastAPI Router: Stripe Webhook Listener & Email Delivery
Path: app/api/v1/webhooks.py
"""
import os
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import stripe

from app.api.deps import get_db
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.download_token import DownloadToken
from app.core.email import send_download_link_email

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.post("/stripe", status_code=status.HTTP_200_OK)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    1. Reads raw binary body from Request.
    2. Validates cryptographically with STRIPE_WEBHOOK_SECRET.
    3. Handles 'checkout.session.completed':
       - Finds Order by stripe_session_id.
       - Marks Order PAID.
       - Increments Product sales_count.
       - Generates 24-hr DownloadToken.
       - Dispatches email with Resend API.
    """
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="STRIPE_WEBHOOK_SECRET is not configured on server."
        )

    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'stripe-signature' header."
        )

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload."
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature."
        )

    # Handle successful checkout session
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        stripe_session_id = session.get("id")

        if not stripe_session_id:
            return {"status": "ignored_no_session_id"}

        # Fetch Order along with product and existing download token
        stmt = (
            select(Order)
            .options(
                selectinload(Order.product),
                selectinload(Order.download_token)
            )
            .where(Order.stripe_session_id == stripe_session_id)
        )
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            # Idempotency safety: If order not found, acknowledge Stripe to prevent retry flood
            return {"status": "order_not_found_logged"}

        # Guard against duplicate webhook deliveries
        if order.status == OrderStatus.PAID and order.download_token:
            return {"status": "already_processed"}

        # 1. Update order status
        order.status = OrderStatus.PAID

        # 2. Increment product sales count
        if order.product:
            order.product.sales_count += 1

        # 3. Create DownloadToken (now + 24 hours)
        token_uuid = uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        download_token = DownloadToken(
            order_id=order.id,
            token=token_uuid,
            expires_at=expires_at,
        )
        db.add(download_token)
        await db.commit()

        # 4. Dispatch Email via Resend API
        download_link = f"{FRONTEND_URL}/download/{token_uuid}"
        try:
            await send_download_link_email(
                to_email=order.buyer_email,
                product_title=order.product.title if order.product else "Your Digital Pattern",
                download_url=download_link,
                expires_at=expires_at
            )
        except Exception as err:
            # Log error but return 200 so Stripe does not retry and re-increment sales
            print(f"[ERROR] Failed to send Resend email: {err}")

    return {"status": "success"}
