"""
SQLAlchemy 2.0 Async Model: Order
Path: app/models/order.py
"""
import enum
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.download_token import DownloadToken

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    buyer_email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    stripe_session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum", native_enum=True),
        default=OrderStatus.PENDING,
        index=True,
        nullable=False
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="orders", lazy="joined")
    download_token: Mapped[Optional["DownloadToken"]] = relationship(
        "DownloadToken", 
        back_populates="order", 
        uselist=False, 
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} email={self.buyer_email!r} status={self.status} amount={self.amount}>"
