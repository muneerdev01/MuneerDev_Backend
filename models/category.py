"""
Category Model
"""
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import JSONB

from .enums import BlogType, EntityType
from .mixins import Base


class Category(Base):
    __tablename__ = "categories"

    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    blog_type = Column(BlogType, nullable=False)
    entity_type = Column(EntityType, nullable=False)
    description = Column(String(1000), nullable=True)
    metadata = Column(JSONB, nullable=True, server_default=text("'{}'"))

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"
