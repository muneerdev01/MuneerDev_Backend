"""
Base Service Class
Common functionality for all services
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T')


class BaseService(Generic[T]):
    """Base service with common CRUD operations"""
    
    def __init__(self, model_class: type[T], session: AsyncSession):
        self.model_class = model_class
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get a single record by ID"""
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records with pagination"""
        result = await self.session.execute(
            select(self.model_class)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new record"""
        obj = self.model_class(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update an existing record"""
        obj = await self.get_by_id(id)
        if not obj:
            return None
        
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def delete(self, id: str) -> bool:
        """Delete a record"""
        obj = await self.get_by_id(id)
        if not obj:
            return False
        
        await self.session.delete(obj)
        await self.session.commit()
        return True
    
    async def count(self) -> int:
        """Get total count of records"""
        result = await self.session.execute(
            select(func.count()).select_from(self.model_class)
        )
        return result.scalar_one()
