"""
Main FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from routers.public.contact import router as contact_router

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Directly import from root level folders
from database.config import get_db
from models import BlogType, ArticleStatus, ContentFormat, EntityType
from config.settings import settings

# Import and include routers
from routers import auth, categories, tags
from routers.public import articles as public_articles
from routers.public import categories as public_categories
from routers.public import tags as public_tags
from routers.public import sitemap
from routers.admin import articles as admin_articles
from routers.media import upload as media_upload
from routers.v1 import checkout, download, products, projects, upload, webhooks


# Modern Lifespan Handler for Startup/Shutdown events
def validate_production_configuration() -> None:
    """Refuse production startup with test payments or missing critical services."""
    problems = []
    if not settings.STRIPE_SECRET_KEY.startswith(("sk_live_", "rk_live_")):
        problems.append("STRIPE_SECRET_KEY must be a live-mode key")
    for name, value in (
        ("STRIPE_WEBHOOK_SECRET", settings.STRIPE_WEBHOOK_SECRET),
        ("SUPABASE_URL", settings.SUPABASE_URL),
        ("SUPABASE_SERVICE_ROLE_KEY", settings.SUPABASE_SERVICE_ROLE_KEY),
        ("RESEND_API_KEY", settings.RESEND_API_KEY),
        ("RESEND_FROM_EMAIL", settings.RESEND_FROM_EMAIL),
        ("ADMIN_EMAIL", settings.ADMIN_EMAIL),
        ("ADMIN_PASSWORD", settings.ADMIN_PASSWORD),
    ):
        if not value:
            problems.append(f"{name} is required")
    if settings.DEBUG:
        problems.append("DEBUG must be false")
    if settings.CORS_ALLOW_CREDENTIALS:
        problems.append("CORS_ALLOW_CREDENTIALS must be false for bearer-token APIs")
    if not settings.FRONTEND_URL.startswith("https://"):
        problems.append("FRONTEND_URL must use HTTPS")
    if not allowed_origins or any(not origin.startswith("https://") for origin in allowed_origins):
        problems.append("ALLOWED_ORIGINS must contain HTTPS origins only")
    if problems:
        raise RuntimeError("Invalid production configuration: " + "; ".join(problems))


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.APP_ENV.lower() == "production":
        validate_production_configuration()
    print("=" * 50)
    print("MuneerDev Blog API Starting...")
    print(f"Version: {settings.APP_VERSION}")
    print(f"App URL: {settings.APP_URL}")
    print(f"Admin Email: {settings.ADMIN_EMAIL}")
    print("=" * 50)
    yield
    print("MuneerDev Blog API Shutting Down...")


# Create FastAPI app
app = FastAPI(
    title="MuneerDev Blog API",
    description="API for managing articles, categories, tags, and content relationships",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


allowed_origins = [
    origin.strip().rstrip("/")
    for origin in settings.ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
if not allowed_origins:
    allowed_origins = ["https://muneerdev.com", "https://www.muneerdev.com"]
if settings.APP_ENV.lower() != "production":
    allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(allowed_origins)),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    if settings.APP_ENV.lower() == "production" and request.url.scheme == "https":
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains",
        )
    return response



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
        result = await db.execute(text("SELECT 1"))
        result.close()
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": settings.APP_VERSION
        }
    except Exception:
        # Do not leak internal error details to the public
        return {
            "status": "unhealthy",
            "database": "disconnected"
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
app.include_router(contact_router, prefix="/api/v1")   # POST /api/v1/contact (Resend)

app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
app.include_router(tags.router, prefix="/api/v1", tags=["tags"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(products.router)
app.include_router(projects.router)
app.include_router(checkout.router)
app.include_router(webhooks.router)
app.include_router(download.router)
app.include_router(upload.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )