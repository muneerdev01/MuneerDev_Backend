"""
ArticleTag - Join Table between Article and Tag
"""
from sqlalchemy import Column, ForeignKey, Table, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .mixins import Base


class ArticleTag(Base):
    __tablename__ = "article_tags"

    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )

    def __repr__(self):
        return f"<ArticleTag(article_id={self.article_id}, tag_id={self.tag_id})>"
