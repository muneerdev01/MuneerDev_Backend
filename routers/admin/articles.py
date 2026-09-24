"""
Admin Articles Router
CRUD operations for articles including drafts and archived
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.config import get_db
from models import Article, Category, ArticleTag, Tag
from models.enums import ArticleStatusEnum, BlogTypeEnum
from services import ArticleService
from security.rbac import require_any_role, require_role
from schemas import ArticleSchema

router = APIRouter(prefix="/admin/articles", tags=["admin-articles"])


@router.get("/", response_model=List[ArticleSchema])
async def list_all_articles(
    status_filter: Optional[ArticleStatusEnum] = Query(None, description="Filter by status"),
    blog_type: Optional[BlogTypeEnum] = Query(None, description="Filter by blog type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_any_role(["ADMIN", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """List all articles including drafts and archived (Admin/Super Admin only)"""
    service = ArticleService(db, user_email=user.get("email"))
    
    query = select(Article)
    
    if status_filter:
        query = query.where(Article.status == status_filter)
    
    if blog_type:
        query = query.where(Article.blog_type == blog_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return [
        await service.format_for_response(article)
        for article in articles
    ]


@router.get("/{article_id}", response_model=ArticleSchema)
async def get_article(
    article_id: str,
    user: dict = Depends(require_any_role(["ADMIN", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """Get any article including drafts (Admin/Super Admin only)"""
    service = ArticleService(db, user_email=user.get("email"))
    article = await service.get_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return await service.format_for_response(article)


@router.post("/", response_model=ArticleSchema, status_code=status.HTTP_201_CREATED)
async def create_article(
    article: ArticleSchema,
    user: dict = Depends(require_any_role(["ADMIN", "EDITOR", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new article (Admin, Editor, Super Admin)"""
    service = ArticleService(db, user_email=user.get("email"))
    
    # Verify category exists
    result = await db.execute(select(Category).where(Category.id == article.category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category_id")
    
    data = article.model_dump(exclude_unset=True)
    db_article = await service.create_with_business_logic(data, user_email=user.get("email"))
    
    return await service.format_for_response(db_article)


@router.put("/{article_id}", response_model=ArticleSchema)
async def update_article(
    article_id: str,
    article: ArticleSchema,
    user: dict = Depends(require_any_role(["ADMIN", "EDITOR", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """Update an article (Admin, Editor, Super Admin)"""
    service = ArticleService(db, user_email=user.get("email"))
    db_article = await service.get_by_id(article_id)
    
    if not db_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Verify category exists
    result = await db.execute(select(Category).where(Category.id == article.category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category_id")
    
    data = article.model_dump(exclude_unset=True)
    db_article = await service.update_with_business_logic(article_id, data, user_email=user.get("email"))
    
    return await service.format_for_response(db_article)


@router.patch("/{article_id}/status", response_model=ArticleSchema)
async def update_article_status(
    article_id: str,
    status: ArticleStatusEnum = Body(..., embed=True),
    user: dict = Depends(require_any_role(["ADMIN", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """Update article status (Admin/Super Admin only)"""
    service = ArticleService(db, user_email=user.get("email"))
    article = await service.get_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article.status = status
    
    if status == ArticleStatusEnum.PUBLISHED.value and not article.published_at:
        article.published_at = service.audit_logger.session.bind.dialect.localtime
        article.published_at = service.audit_logger.session.execute("SELECT CURRENT_TIMESTAMP").scalar()
    
    await db.commit()
    await db.refresh(article)
    
    # Log audit event
    if status == ArticleStatusEnum.PUBLISHED.value:
        await service.audit_logger.log_publish(
            entity_type=ArticleStatus,
            entity_id=str(article.id),
            user_email=user.get("email"),
            entity_name=article.title,
            details={"status": status}
        )
    elif status == ArticleStatusEnum.ARCHIVED.value:
        await service.audit_logger.log_archive(
            entity_type=ArticleStatus,
            entity_id=str(article.id),
            user_email=user.get("email"),
            entity_name=article.title,
            details={"status": status}
        )
    
    return await service.format_for_response(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: str,
    user: dict = Depends(require_role("SUPER_ADMIN")),
    db: AsyncSession = Depends(get_db)
):
    """Delete an article (Super Admin only)"""
    service = ArticleService(db, user_email=user.get("email"))
    
    if not await service.delete(article_id, user_email=user.get("email")):
        raise HTTPException(status_code=404, detail="Article not found")
    
    return None


@router.post("/{article_id}/tags/{tag_id}", status_code=status.HTTP_201_CREATED)
async def add_tag(
    article_id: str,
    tag_id: str,
    user: dict = Depends(require_any_role(["ADMIN", "EDITOR", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """Add a tag to an article"""
    service = ArticleService(db, user_email=user.get("email"))
    
    if not await service.add_tag(article_id, tag_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag already associated with article"
        )
    
    return {"message": "Tag added successfully"}


@router.delete("/{article_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag(
    article_id: str,
    tag_id: str,
    user: dict = Depends(require_any_role(["ADMIN", "EDITOR", "SUPER_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):
    """Remove a tag from an article"""
    service = ArticleService(db, user_email=user.get("email"))
    
    if not await service.remove_tag(article_id, tag_id):
        raise HTTPException(status_code=404, detail="Tag not associated with article")
    
    return None
