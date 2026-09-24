"""
AuditLog Model
"""
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID

from .mixins import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    user_email = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity_id={self.entity_id})>"
