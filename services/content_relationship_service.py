"""
ContentRelationship Service
CRUD operations for polymorphic relationships
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from models import ContentRelationship, Article
from models.enums import EntityType
from services.base_service import BaseService


class ContentRelationshipService(BaseService[ContentRelationship]):
    """Service for content relationship CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ContentRelationship, session)
    
    async def get_by_source(
        self,
        source_type: EntityType,
        source_id: str,
        limit: int = 100
    ) -> List[ContentRelationship]:
        """Get all relationships from a source entity"""
        result = await self.session.execute(
            select(ContentRelationship)
            .where(
                ContentRelationship.source_type == source_type,
                ContentRelationship.source_id == source_id
            )
            .order_by(ContentRelationship.display_order)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_target(
        self,
        target_type: EntityType,
        target_id: str,
        limit: int = 100
    ) -> List[ContentRelationship]:
        """Get all relationships to a target entity"""
        result = await self.session.execute(
            select(ContentRelationship)
            .where(
                ContentRelationship.target_type == target_type,
                ContentRelationship.target_id == target_id
            )
            .order_by(ContentRelationship.display_order)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_relationship(
        self,
        source_type: EntityType,
        source_id: str,
        target_type: EntityType,
        target_id: str,
        relationship_type: str,
        display_order: int = 0,
        metadata: Dict[str, Any] = None
    ) -> ContentRelationship:
        """Create a new content relationship"""
        data = {
            "source_type": source_type,
            "source_id": source_id,
            "target_type": target_type,
            "target_id": target_id,
            "relationship_type": relationship_type,
            "display_order": display_order,
            "metadata": metadata or {}
        }
        return await self.create(data)
    
    async def reorder_relationships(
        self,
        source_type: EntityType,
        source_id: str,
        relationships: List[Dict[str, Any]]
    ) -> bool:
        """
        Reorder relationships for a source entity.
        
        Args:
            source_type: Type of source entity
            source_id: ID of source entity
            relationships: List of {id, display_order} dicts
            
        Returns:
            True if successful
        """
        # Update each relationship
        for rel_data in relationships:
            rel_id = rel_data.get("id")
            new_order = rel_data.get("display_order", 0)
            
            if rel_id:
                result = await self.session.execute(
                    select(ContentRelationship)
                    .where(
                        ContentRelationship.id == rel_id,
                        ContentRelationship.source_type == source_type,
                        ContentRelationship.source_id == source_id
                    )
                )
                relationship = result.scalar_one_or_none()
                
                if relationship:
                    relationship.display_order = new_order
        
        await self.session.commit()
        return True
    
    async def delete_by_source(
        self,
        source_type: EntityType,
        source_id: str
    ) -> int:
        """Delete all relationships from a source entity"""
        result = await self.session.execute(
            select(ContentRelationship).where(
                ContentRelationship.source_type == source_type,
                ContentRelationship.source_id == source_id
            )
        )
        relationships = result.scalars().all()
        
        for rel in relationships:
            await self.session.delete(rel)
        
        await self.session.commit()
        return len(relationships)
    
    async def get_related_articles(
        self,
        source_type: EntityType,
        source_id: str,
        relationship_type: str = None
    ) -> List[Article]:
        """Get articles related to a source entity"""
        from models import Article, ContentRelationship
        
        query = select(Article).join_from(
            Article, ContentRelationship,
            Article.id == ContentRelationship.target_id
        ).where(
            ContentRelationship.source_type == source_type,
            ContentRelationship.source_id == source_id,
            ContentRelationship.target_type == EntityType.article,
            Article.status == "PUBLISHED"
        )
        
        if relationship_type:
            query = query.where(ContentRelationship.relationship_type == relationship_type)
        
        result = await self.session.execute(query)
        return result.scalars().all()
