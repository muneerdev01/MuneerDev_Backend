"""
Category Service
CRUD operations for categories with validation
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Category
from models.enums import BlogType, EntityType
from utils.slug_generator import generate_unique_slug, check_slug_exists
from services.base_service import BaseService


class CategoryService(BaseService[Category]):
    """Service for category CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Category, session)
    
    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug"""
        result = await self.session.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def list_by_blog_type(self, blog_type: BlogType) -> List[Category]:
        """List categories by blog type"""
        result = await self.session.execute(
            select(Category).where(Category.blog_type == blog_type)
        )
        return result.scalars().all()
    
    async def list_by_entity_type(self, entity_type: EntityType) -> List[Category]:
        """List categories by entity type"""
        result = await self.session.execute(
            select(Category).where(Category.entity_type == entity_type)
        )
        return result.scalars().all()
    
    async def create_with_slug(self, data: Dict[str, Any]) -> Category:
        """Create category with auto-generated slug"""
        # Generate unique slug from name
        slug = await generate_unique_slug(
            self.session, Category, data.get("name", "")
        )
        data["slug"] = slug
        
        return await self.create(data)
    
    async def update_with_slug(self, id: str, data: Dict[str, Any]) -> Optional[Category]:
        """Update category with slug regeneration if name changed"""
        if "name" in data and data["name"]:
            # Generate new slug
            slug = await generate_unique_slug(
                self.session, Category, data["name"], exclude_id=id
            )
            data["slug"] = slug
        
        return await self.update(id, data)
