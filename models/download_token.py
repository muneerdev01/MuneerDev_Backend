"""
SQLAlchemy 2.0 Async Model: DownloadToken
Path: app/models/download_token.py
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.order import Order

def default_expiry() -> datetime:
    """Generates UTC expiration timestamp 24 hours from creation."""
    return datetime.now(timezone.utc) + timedelta(hours=24)

class DownloadToken(Base):
    __tablename__ = "download_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    # Unique cryptographically secure UUID token
    token: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        default=uuid.uuid4, 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    # 24-hour expiry threshold
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=default_expiry, 
        nullable=False
    )

    # Relationship
    order: Mapped["Order"] = relationship("Order", back_populates="download_token")

    @property
    def is_expired(self) -> bool:
        """Helper to verify expiration against current UTC time."""
        current_time = datetime.now(timezone.utc)
        target = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
        return current_time > target

    def __repr__(self) -> str:
        return f"<DownloadToken id={self.id} token={self.token} expired={self.is_expired}>"
