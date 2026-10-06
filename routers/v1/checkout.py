"""
FastAPI Router: Stripe Checkout Session Creation
Path: app/api/v1/checkout.py
"""
import os
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from app.api.deps import get_db
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.schemas.order import CheckoutRequest, CheckoutResponse

router = APIRouter(prefix="/api/checkout", tags=["checkout"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.post("", response_model=CheckoutResponse, status_code=status.HTTP_200_OK)
async def create_checkout_session(
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    1. Validates product slug and ensures active status.
    2. Converts price to cents for Stripe.
    3. Creates a Stripe Checkout Session with customer email and metadata.
    4. Records an Order with status=PENDING in the database.
    5. Returns the Stripe checkout URL.
    """
    if not stripe.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe API key is not configured on the server."
        )

    # 1. Fetch product
    stmt = select(Product).where(Product.slug == payload.product_slug, Product.is_active == True)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{payload.product_slug}' not found or is currently inactive."
        )

    # 2. Calculate unit amount in cents (e.g. $8.50 -> 850)
    unit_amount_cents = int(product.price * 100)

    # 3. Create Stripe Checkout Session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=payload.buyer_email,
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": unit_amount_cents,
                        "product_data": {
                            "name": product.title,
                            "description": f"Instant digital download ({product.category.value})",
                            "images": product.preview_images[:1] if product.preview_images else [],
                        },
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "product_id": str(product.id),
                "product_slug": product.slug,
                "buyer_email": payload.buyer_email,
            },
            success_url=f"{FRONTEND_URL}/download/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/shop/{product.slug}?canceled=true",
        )
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe session creation error: {str(e.user_message or e)}"
        )

    # 4. Insert PENDING order in DB
    order = Order(
        product_id=product.id,
        buyer_email=payload.buyer_email,
        stripe_session_id=session.id,
        amount=product.price,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    await db.commit()

    return CheckoutResponse(
        checkout_url=session.url,
        session_id=session.id
    )
