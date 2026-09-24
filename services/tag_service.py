"""
Tag Service
CRUD operations for tags with validation
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Tag
from utils.slug_generator import generate_unique_slug
from services.base_service import BaseService


class TagService(BaseService[Tag]):
    """Service for tag CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Tag, session)
    
    async def get_by_slug(self, slug: str) -> Optional[Tag]:
        """Get tag by slug"""
        result = await self.session.execute(
            select(Tag).where(Tag.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def create_with_slug(self, data: Dict[str, Any]) -> Tag:
        """Create tag with auto-generated slug"""
        # Generate unique slug from name
        slug = await generate_unique_slug(
            self.session, Tag, data.get("name", "")
        )
        data["slug"] = slug
        
        return await self.create(data)
    
    async def update_with_slug(self, id: str, data: Dict[str, Any]) -> Optional[Tag]:
        """Update tag with slug regeneration if name changed"""
        if "name" in data and data["name"]:
            slug = await generate_unique_slug(
                self.session, Tag, data["name"], exclude_id=id
            )
            data["slug"] = slug
        
        return await self.update(id, data)
    
    async def add_tag_to_article(self, article_id: str, tag_id: str) -> bool:
        """Add a tag to an article"""
        from models import ArticleTag
        
        # Check if relationship already exists
        result = await self.session.execute(
            select(ArticleTag).where(
                ArticleTag.article_id == article_id,
                ArticleTag.tag_id == tag_id
            )
        )
        if result.scalar_one_or_none():
            return False
        
        # Create relationship
        article_tag = ArticleTag(
            article_id=article_id,
            tag_id=tag_id
        )
        self.session.add(article_tag)
        await self.session.commit()
        return True
    
    async def remove_tag_from_article(self, article_id: str, tag_id: str) -> bool:
        """Remove a tag from an article"""
        from models import ArticleTag
        
        result = await self.session.execute(
            select(ArticleTag).where(
                ArticleTag.article_id == article_id,
                ArticleTag.tag_id == tag_id
            )
        )
        article_tag = result.scalar_one_or_none()
        
        if not article_tag:
            return False
        
        await self.session.delete(article_tag)
        await self.session.commit()
        return True
    
    async def get_article_tags(self, article_id: str) -> List[Tag]:
        """Get all tags for an article"""
        result = await self.session.execute(
            select(Tag)
            .join_from(Tag, ArticleTag)
            .where(ArticleTag.article_id == article_id)
        )
        return result.scalars().all()
