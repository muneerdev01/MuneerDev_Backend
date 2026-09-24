"""
ContentRelationship - Polymorphic Connectivity Table
"""
from sqlalchemy import Column, String, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID

from .enums import EntityType
from .mixins import Base


class ContentRelationship(Base):
    __tablename__ = "content_relationships"

    source_type = Column(EntityType, nullable=False)
    source_id = Column(UUID(as_uuid=True), nullable=False)
    target_type = Column(EntityType, nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return (
            f"<ContentRelationship(id={self.id}, "
            f"source={self.source_type}:{self.source_id}, "
            f"target={self.target_type}:{self.target_id})>"
        )
