"""Shared dependencies for the API v1 routers."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client, create_client

from config.settings import settings
from database.config import get_db as get_database_session
from security.rbac import require_any_role

security = HTTPBearer(auto_error=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_database_session():
        yield session


def get_supabase_client() -> Client:
    """Create a server-side Supabase client using only the service-role secret."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Storage is not configured.",
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


async def get_current_admin(
    user: dict = Depends(require_any_role(["ADMIN", "SUPER_ADMIN"])),
) -> dict:
    """Require a verified administrator JWT for admin-only routes."""
    return user
