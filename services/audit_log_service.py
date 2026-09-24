"""
AuditLog Service
CRUD operations for audit logs
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models import AuditLog
from services.base_service import BaseService


class AuditLogService(BaseService[AuditLog]):
    """Service for audit log CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)
    
    async def create_log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_email: str,
        details: Dict[str, Any] = None
    ) -> AuditLog:
        """Create a new audit log entry"""
        data = {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_email": user_email,
            "details": details or {}
        }
        return await self.create(data)
    
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get audit logs for an entity"""
        result = await self.session.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_user(
        self,
        user_email: str,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get audit logs for a user"""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_email == user_email)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_action(
        self,
        action: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs for a specific action"""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
