"""
FastAPI Router: Stripe Webhook Listener & Email Delivery
Path: app/api/v1/webhooks.py
"""
import uuid
from datetime import datetime, timezone, timedelta
import logging
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import stripe

from config.settings import settings
from database.config import get_db
from models.order import Order, OrderStatus
from models.download_token import DownloadToken
from core.email import send_download_link_email

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET
FRONTEND_URL = settings.FRONTEND_URL.rstrip("/")

@router.post("/stripe", status_code=status.HTTP_200_OK)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
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

    event_type = event["type"]

    if event_type in {"checkout.session.expired", "checkout.session.async_payment_failed"}:
        failed_session = event["data"]["object"]
        session_id = failed_session.get("id")
        if session_id:
            result = await db.execute(
                select(Order)
                .where(Order.stripe_session_id == session_id)
                .with_for_update(of=Order)
            )
            order = result.scalar_one_or_none()
            if order and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.FAILED
                await db.commit()
        return {"status": "failure_recorded"}

    if event_type in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        session = event["data"]["object"]
        stripe_session_id = session.get("id")

        if not stripe_session_id:
            logger.error("Completed Stripe Checkout event has no session ID")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stripe Checkout event is missing its session ID.",
            )

        # Fetch Order along with product and existing download token
        stmt = (
            select(Order)
            .options(
                selectinload(Order.product),
                selectinload(Order.download_token)
            )
            .where(Order.stripe_session_id == stripe_session_id)
            .with_for_update(of=Order)
        )
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            logger.error("No order matches a completed Stripe Checkout Session")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No matching order was found for the completed payment.",
            )

        # A completed Checkout Session must also report a paid payment.
        if session.get("payment_status") != "paid":
            return {"status": "payment_not_paid"}

        expected_amount = int(order.amount * 100)
        if (
            session.get("amount_total") != expected_amount
            or str(session.get("currency", "")).lower() != "usd"
        ):
            logger.error("Stripe session amount/currency did not match order %s", order.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stripe session does not match the recorded order.",
            )

        already_paid = order.status == OrderStatus.PAID
        if already_paid and order.download_token and order.email_sent_at:
            return {"status": "already_processed"}

        if not already_paid:
            order.status = OrderStatus.PAID
            if order.product:
                order.product.sales_count += 1

        if order.download_token:
            download_token = order.download_token
            expires_at = download_token.expires_at
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            download_token = DownloadToken(
                order_id=order.id,
                token=uuid.uuid4(),
                expires_at=expires_at,
            )
            db.add(download_token)
            await db.flush()

        # Keep the order row locked until the mail result is recorded. If mail
        # fails, the transaction rolls back and Stripe's retry can retry safely.
        download_link = f"{FRONTEND_URL}/download/{download_token.token}"
        try:
            await send_download_link_email(
                to_email=order.buyer_email,
                product_title=order.product.title if order.product else "Your Digital Pattern",
                download_url=download_link,
                expires_at=expires_at
            )
        except Exception as err:
            logger.exception("Failed to send purchase email for order %s", order.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Purchase email delivery failed; Stripe should retry the event.",
            ) from err

        order.email_sent_at = datetime.now(timezone.utc)
        await db.commit()

    return {"status": "success"}
