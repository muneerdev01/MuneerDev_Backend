"""
Main FastAPI Application Entry Point
"""
import os
import sys

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Directly import from root level folders
from database.config import engine, get_db
from models import (
    BlogType, ArticleStatus, ContentFormat, EntityType,
    Category, Tag, Article, ArticleTag,
    ContentRelationship, MediaAsset, AuditLog
)
from config.settings import settings

# Import and include routers
from routers import articles, categories, tags, auth
from routers.public import articles as public_articles
from routers.public import categories as public_categories
from routers.public import tags as public_tags
from routers.public import sitemap
from routers.admin import articles as admin_articles
from routers.media import upload as media_upload

# Create FastAPI app
app = FastAPI(
    title="MuneerDev Blog API",
    description="API for managing articles, categories, tags, and content relationships",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Configure CORS - Allow localhost:3000 and muneerdev.com
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://muneerdev.com",
    "https://www.muneerdev.com",
    settings.NEXT_PUBLIC_APP_URL,
    settings.APP_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 50)
    print("MuneerDev Blog API Starting...")
    print(f"Version: {settings.APP_VERSION}")
    print(f"App URL: {settings.APP_URL}")
    print(f"Admin Email: {settings.ADMIN_EMAIL}")
    print("=" * 50)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MuneerDev Blog API",
        "version": "1.0.0",
        "docs": "/docs",
        "author": {
            "name": settings.SITE_AUTHOR,
            "email": settings.SITE_AUTHOR_EMAIL,
            "whatsapp": settings.SITE_AUTHOR_WHATSAPP
        },
        "domain": settings.PRIMARY_DOMAIN
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        result = await db.execute("SELECT 1")
        result.close()
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": settings.APP_VERSION
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"disconnected: {str(e)}"
        }


@app.get("/enums")
async def get_enums():
    """Get all available enums"""
    return {
        "blog_types": [BlogType.TECH.name, BlogType.HEALTHCARE.name],
        "article_statuses": [ArticleStatus.DRAFT.name, ArticleStatus.PUBLISHED.name, ArticleStatus.ARCHIVED.name],
        "content_formats": [ContentFormat.markdown.name, ContentFormat.html.name, ContentFormat.rich_text.name],
        "entity_types": [EntityType.article.name, EntityType.project.name, EntityType.service.name, EntityType.resource.name, EntityType.product.name, EntityType.customer.name, EntityType.lead.name]
    }


@app.get("/site-info")
async def get_site_info():
    """Get site configuration info (public)"""
    return {
        "name": settings.APP_NAME,
        "author": settings.SITE_AUTHOR,
        "author_email": settings.SITE_AUTHOR_EMAIL,
        "author_whatsapp": settings.SITE_AUTHOR_WHATSAPP,
        "domain": settings.PRIMARY_DOMAIN
    }


# Include all routers
app.include_router(public_articles.router)
app.include_router(public_categories.router)
app.include_router(public_tags.router)
app.include_router(sitemap.router)

app.include_router(admin_articles.router)
app.include_router(media_upload.router)

app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
app.include_router(tags.router, prefix="/api/v1", tags=["tags"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
