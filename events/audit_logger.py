"""
Audit Logger
Automatically writes to audit_logs table on entity changes
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditLog
from models.enums import EntityType


class AuditLogger:
    """
    Audit logger that automatically records entity changes.
    Use as a mixin or standalone service.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize audit logger.
        
        Args:
            session: Database session for writing audit logs
        """
        self.session = session
    
    async def log_action(
        self,
        action: str,
        entity_type: EntityType,
        entity_id: str,
        user_email: str,
        details: Dict[str, Any] = None,
        entity_name: str = None
    ) -> AuditLog:
        """
        Log an action to the audit log table.
        
        Args:
            action: Action performed (create, update, delete, publish, archive)
            entity_type: Type of entity being modified
            entity_id: ID of the entity
            user_email: Email of the user performing the action
            details: Additional details about the change
            entity_name: Optional human-readable entity name
            
        Returns:
            Created AuditLog object
        """
        audit_log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            details={
                "entity_name": entity_name,
                **(details or {})
            }
        )
        
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        
        return audit_log
    
    async def log_create(
        self,
        entity_type: EntityType,
        entity_id: str,
        user_email: str,
        entity_name: str = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Log entity creation"""
        return await self.log_action(
            action="CREATE",
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            details={
                **(details or {}),
                "action_description": f"Created {entity_type} entity"
            },
            entity_name=entity_name
        )
    
    async def log_update(
        self,
        entity_type: EntityType,
        entity_id: str,
        user_email: str,
        entity_name: str = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Log entity update"""
        return await self.log_action(
            action="UPDATE",
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            details={
                **(details or {}),
                "action_description": f"Updated {entity_type} entity"
            },
            entity_name=entity_name
        )
    
    async def log_delete(
        self,
        entity_type: EntityType,
        entity_id: str,
        user_email: str,
        entity_name: str = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Log entity deletion"""
        return await self.log_action(
            action="DELETE",
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            details={
                **(details or {}),
                "action_description": f"Deleted {entity_type} entity"
            },
            entity_name=entity_name
        )
    
    async def log_publish(
        self,
        entity_type: EntityType,
        entity_id: str,
        user_email: str,
        entity_name: str = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Log entity publish action"""
        return await self.log_action(
            action="PUBLISH",
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            details={
                **(details or {}),
                "action_description": f"Published {entity_type} entity",
                "status": "PUBLISHED"
            },
            entity_name=entity_name
        )
    
    async def log_archive(
        self,
        entity_type: EntityType,
        entity_id: str,
        user_email: str,
        entity_name: str = None,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Log entity archive action"""
        return await self.log_action(
            action="ARCHIVE",
            entity_type=entity_type,
            entity_id=entity_id,
            user_email=user_email,
            details={
                **(details or {}),
                "action_description": f"Archived {entity_type} entity",
                "status": "ARCHIVED"
            },
            entity_name=entity_name
        )
    
    async def log_bulk_action(
        self,
        action: str,
        entity_type: EntityType,
        entity_ids: list,
        user_email: str,
        details: Dict[str, Any] = None
    ) -> list:
        """Log multiple actions at once"""
        audit_logs = []
        
        for entity_id in entity_ids:
            audit_log = await self.log_action(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                user_email=user_email,
                details=details
            )
            audit_logs.append(audit_log)
        
        return audit_logs


class AuditLoggerMixin:
    """
    Mixin for models that need audit logging.
    Add this to models that should be logged.
    
    Usage:
        class Article(Base, AuditLoggerMixin):
            # Your model fields...
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._audit_logger: Optional[AuditLogger] = None
    
    def set_audit_logger(self, logger: AuditLogger):
        """Set the audit logger for this instance"""
        self._audit_logger = logger
    
    async def log_create(self, user_email: str, entity_name: str = None):
        """Log creation of this entity"""
        if self._audit_logger:
            await self._audit_logger.log_create(
                entity_type=self.__class__.__name__.lower(),
                entity_id=str(self.id),
                user_email=user_email,
                entity_name=entity_name
            )
    
    async def log_update(self, user_email: str, entity_name: str = None):
        """Log update of this entity"""
        if self._audit_logger:
            await self._audit_logger.log_update(
                entity_type=self.__class__.__name__.lower(),
                entity_id=str(self.id),
                user_email=user_email,
                entity_name=entity_name
            )
    
    async def log_delete(self, user_email: str, entity_name: str = None):
        """Log deletion of this entity"""
        if self._audit_logger:
            await self._audit_logger.log_delete(
                entity_type=self.__class__.__name__.lower(),
                entity_id=str(self.id),
                user_email=user_email,
                entity_name=entity_name
            )
