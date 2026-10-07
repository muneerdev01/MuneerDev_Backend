"""
Pydantic v2 Schemas: Order & Checkout
Path: app/schemas/order.py
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from models.order import OrderStatus
from schemas.product import ProductPublicCard

class CheckoutRequest(BaseModel):
    """Payload sent from Next.js 15 shop detail page to initiate Stripe Checkout."""
    product_slug: str = Field(..., example="nordic-cable-knit-sweater-pattern")
    buyer_email: EmailStr = Field(..., example="craftmaker@gmail.com")

class CheckoutResponse(BaseModel):
    """FastAPI response returning Stripe redirect URL and session ID."""
    checkout_url: str
    session_id: str

class OrderRead(BaseModel):
    id: int
    product_id: int
    buyer_email: EmailStr
    stripe_session_id: str
    amount: Decimal
    status: OrderStatus
    created_at: datetime
    product: Optional[ProductPublicCard] = None

    model_config = ConfigDict(from_attributes=True)
