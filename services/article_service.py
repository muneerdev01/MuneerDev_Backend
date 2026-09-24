"""
Article Service
Core business logic for articles including slug generation, TOC extraction,
reading time calculation, and draft protection
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from models import Article, ArticleTag, Category, Tag, AuditLog
from models.enums import ArticleStatus, BlogType, EntityType
from utils.slug_generator import generate_unique_slug
from utils.reading_time import calculate_reading_time
from utils.toc_extractor import extract_toc
from utils.healthcare_safeguards import (
    validate_healthcare_content,
    add_healthcare_disclaimer,
    format_healthcare_payload,
    strip_healthcare_metadata
)
from services.base_service import BaseService
from events import AuditLogger


class ArticleService(BaseService[Article]):
    """Service for article CRUD operations with business logic"""
    
    def __init__(self, session: AsyncSession, user_email: str = None):
        super().__init__(Article, session)
        self.audit_logger = AuditLogger(session)
        self.user_email = user_email or "system"
    
    async def get_by_slug(self, slug: str, include_drafts: bool = False) -> Optional[Article]:
        """Get article by slug with optional draft inclusion"""
        query = select(Article).where(Article.slug == slug)
        
        if not include_drafts:
            query = query.where(Article.status == ArticleStatus.PUBLISHED)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_published_by_slug(self, slug: str) -> Optional[Article]:
        """Get only published article by slug (draft protection)"""
        return await self.get_by_slug(slug, include_drafts=False)
    
    async def list_published(
        self,
        skip: int = 0,
        limit: int = 10,
        blog_type: BlogType = None,
        category_id: str = None
    ) -> List[Article]:
        """List only published articles with optional filters"""
        query = select(Article).where(Article.status == ArticleStatus.PUBLISHED)
        
        if blog_type:
            query = query.where(Article.blog_type == blog_type)
        
        if category_id:
            query = query.where(Article.category_id == category_id)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_with_business_logic(
        self,
        data: Dict[str, Any],
        user_email: str = None
    ) -> Article:
        """Create article with all business logic applied and audit logging"""
        user_email = user_email or self.user_email
        
        # Generate unique slug from title
        slug = await generate_unique_slug(
            self.session, Article, data.get("title", "")
        )
        data["slug"] = slug
        
        # Calculate reading time if not provided
        if "reading_time" not in data or not data["reading_time"]:
            data["reading_time"] = calculate_reading_time(data.get("content", ""))
        
        # Extract table of contents if content provided
        if "content" in data and "content_format" in data:
            content_format = data.get("content_format", "markdown")
            data["table_of_contents"] = extract_toc(
                data["content"],
                content_format
            )
        
        # Validate healthcare content if applicable
        if data.get("blog_type") == BlogType.HEALTHCARE:
            is_valid, errors = validate_healthcare_content(data)
            if not is_valid:
                raise ValueError(f"Healthcare content validation failed: {errors}")
        
        # Create article
        article = await self.create(data)
        
        # Log audit event
        await self.audit_logger.log_create(
            entity_type=EntityType.article,
            entity_id=str(article.id),
            user_email=user_email,
            entity_name=article.title,
            details={"content_format": data.get("content_format")}
        )
        
        return article
    
    async def update_with_business_logic(
        self,
        id: str,
        data: Dict[str, Any],
        user_email: str = None
    ) -> Optional[Article]:
        """Update article with business logic applied and audit logging"""
        user_email = user_email or self.user_email
        
        article = await self.get_by_id(id)
        if not article:
            return None
        
        # Regenerate slug if title changed
        if "title" in data and data["title"]:
            slug = await generate_unique_slug(
                self.session, Article, data["title"], exclude_id=id
            )
            data["slug"] = slug
        
        # Recalculate reading time if content changed
        if "content" in data and "content_format" in data:
            data["reading_time"] = calculate_reading_time(data["content"])
            
            # Extract updated TOC
            content_format = data.get("content_format", "markdown")
            data["table_of_contents"] = extract_toc(
                data["content"],
                content_format
            )
        
        # Validate healthcare content if blog_type is healthcare
        if data.get("blog_type") == BlogType.HEALTHCARE:
            is_valid, errors = validate_healthcare_content(data)
            if not is_valid:
                raise ValueError(f"Healthcare content validation failed: {errors}")
        
        # Update article
        updated_article = await self.update(id, data)
        
        # Log audit event
        await self.audit_logger.log_update(
            entity_type=EntityType.article,
            entity_id=str(article.id),
            user_email=user_email,
            entity_name=updated_article.title,
            details={
                "changed_fields": list(data.keys()),
                "content_format": data.get("content_format")
            }
        )
        
        return updated_article
    
    async def publish_article(
        self,
        id: str,
        user_email: str = None
    ) -> Optional[Article]:
        """Publish an article (set status to PUBLISHED)"""
        user_email = user_email or self.user_email
        
        article = await self.get_by_id(id)
        if not article:
            return None
        
        article.status = ArticleStatus.PUBLISHED
        article.published_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(article)
        
        # Log audit event
        await self.audit_logger.log_publish(
            entity_type=EntityType.article,
            entity_id=str(article.id),
            user_email=user_email,
            entity_name=article.title,
            details={"status": "PUBLISHED"}
        )
        
        return article
    
    async def archive_article(
        self,
        id: str,
        user_email: str = None
    ) -> Optional[Article]:
        """Archive an article (set status to ARCHIVED)"""
        user_email = user_email or self.user_email
        
        article = await self.get_by_id(id)
        if not article:
            return None
        
        article.status = ArticleStatus.ARCHIVED
        
        await self.session.commit()
        await self.session.refresh(article)
        
        # Log audit event
        await self.audit_logger.log_archive(
            entity_type=EntityType.article,
            entity_id=str(article.id),
            user_email=user_email,
            entity_name=article.title,
            details={"status": "ARCHIVED"}
        )
        
        return article
    
    async def delete_article(
        self,
        id: str,
        user_email: str = None
    ) -> bool:
        """Delete an article with audit logging"""
        user_email = user_email or self.user_email
        
        article = await self.get_by_id(id)
        if not article:
            return False
        
        article_title = article.title
        
        await self.session.delete(article)
        await self.session.commit()
        
        # Log audit event
        await self.audit_logger.log_delete(
            entity_type=EntityType.article,
            entity_id=str(article.id),
            user_email=user_email,
            entity_name=article_title,
            details={"status": "DELETED"}
        )
        
        return True
    
    async def add_tag(self, article_id: str, tag_id: str) -> bool:
        """Add a tag to an article"""
        # Check if article exists and is accessible
        article = await self.get_by_id(article_id)
        if not article:
            return False
        
        # Create relationship
        article_tag = ArticleTag(article_id=article_id, tag_id=tag_id)
        self.session.add(article_tag)
        await self.session.commit()
        return True
    
    async def remove_tag(self, article_id: str, tag_id: str) -> bool:
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
    
    async def get_tags(self, article_id: str) -> List[Tag]:
        """Get all tags for an article"""
        result = await self.session.execute(
            select(Tag)
            .join_from(Tag, ArticleTag)
            .where(ArticleTag.article_id == article_id)
        )
        return result.scalars().all()
    
    async def format_for_response(
        self,
        article: Article,
        include_healthcare_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Format article for API response with healthcare safeguards.
        
        Args:
            article: Database article object
            include_healthcare_metadata: Include healthcare-specific metadata
            
        Returns:
            Formatted article dictionary
        """
        # Convert to dict
        article_dict = {
            "id": str(article.id),
            "slug": article.slug,
            "title": article.title,
            "excerpt": article.excerpt,
            "content": article.content,
            "content_format": article.content_format.value if article.content_format else None,
            "blog_type": article.blog_type.value if article.blog_type else None,
            "category_id": str(article.category_id) if article.category_id else None,
            "status": article.status.value if article.status else None,
            "reading_time": article.reading_time,
            "featured": article.featured,
            "featured_image": article.featured_image,
            "image_alt_text": article.image_alt_text,
            "seo_title": article.seo_title,
            "seo_description": article.seo_description,
            "canonical_url": article.canonical_url,
            "og_image": article.og_image,
            "author": article.author or {},
            "table_of_contents": article.table_of_contents or [],
            "references": article.references or [],
            "published_at": article.published_at,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "created_by": str(article.created_by) if article.created_by else None,
            "updated_by": str(article.updated_by) if article.updated_by else None,
        }
        
        # Add healthcare safeguards if applicable
        if article.blog_type == BlogType.HEALTHCARE:
            article_dict = format_healthcare_payload(
                article_dict,
                include_disclaimer=include_healthcare_metadata
            )
        
        return article_dict
