"""
SQLAlchemy 2.0 Async Model: Product
Path: app/models/product.py
"""
import enum
from decimal import Decimal
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, Numeric, Integer, Boolean, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order

class ProductCategory(str, enum.Enum):
    PATTERNS = "PATTERNS"
    TEMPLATES = "TEMPLATES"
    EBOOKS = "EBOOKS"

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(250), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    category: Mapped[ProductCategory] = mapped_column(
        SAEnum(ProductCategory, name="product_category_enum", native_enum=True),
        nullable=False,
        index=True
    )
    
    # Public preview image URLs JSON array
    preview_images: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Private storage file path in Supabase Storage bucket (e.g., 'products/patterns/cable_knit.pdf')
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Size in bytes
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    sales_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order", 
        back_populates="product", 
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} slug={self.slug!r} price={self.price} sales={self.sales_count}>"
