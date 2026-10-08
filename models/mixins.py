"""
Database Mixins and Base Models
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin

from database.base import Base as MetadataBase


@declarative_mixin
class UUIDMixin:
    """Mixin to add UUID primary key to models"""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )


@declarative_mixin
class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
    )


@declarative_mixin
class AuditMixin:
    """Mixin to add created_by and updated_by tracking"""

    created_by = Column(
        UUID(as_uuid=True),
        nullable=False,
    )
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=False,
    )


# Base class combining all mixins
class Base(MetadataBase, UUIDMixin, TimestampMixin):
    """Base class for all models with UUID, timestamps"""
    __abstract__ = True
