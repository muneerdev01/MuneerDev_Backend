"""
Article Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .enums import BlogType, ArticleStatus, ContentFormat, ArticleStatusEnum
from .mixins import Base


class Article(Base):
    __tablename__ = "articles"

    slug = Column(String(255), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    excerpt = Column(String(1000), nullable=False)
    content = Column(Text, nullable=False)
    content_format = Column(ContentFormat, nullable=False)
    blog_type = Column(BlogType, nullable=False)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(ArticleStatus, default=ArticleStatusEnum.DRAFT, nullable=False)
    reading_time = Column(Integer, default=0, nullable=False)
    featured = Column(Boolean, default=False, nullable=False)
    featured_image = Column(String(1000), nullable=True)
    image_alt_text = Column(String(500), nullable=True)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    canonical_url = Column(String(1000), nullable=True)
    og_image = Column(String(1000), nullable=True)

    # JSON fields
    author = Column(JSONB, nullable=False, server_default='{"name": "", "email": ""}')
    table_of_contents = Column(JSONB, nullable=True, server_default="[]")
    references = Column(JSONB, nullable=True, server_default="[]")

    published_at = Column(DateTime, nullable=True)

    # Relationships
    category = relationship("Category", backref="articles")
    tags = relationship(
        "Tag",
        secondary="article_tags",
        backref="articles",
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}', slug='{self.slug}')>"
