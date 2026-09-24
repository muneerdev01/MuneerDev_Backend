"""
Tag Model
"""
from sqlalchemy import Column, String

from .mixins import Base


class Tag(Base):
    __tablename__ = "tags"

    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', slug='{self.slug}')>"
