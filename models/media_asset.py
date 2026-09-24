"""
MediaAsset Model
"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .mixins import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    file_name = Column(String(255), nullable=False)
    original_name = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    alt_text = Column(String(500), nullable=True)
    caption = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<MediaAsset(id={self.id}, file_name='{self.file_name}')>"
