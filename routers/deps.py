"""
FastAPI Dependencies: DB Session, Admin Auth, and Supabase Client
Path: app/api/deps.py
"""
import os
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from supabase import create_client, Client

security = HTTPBearer(auto_error=True)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
ADMIN_SECRET_TOKEN = os.getenv("ADMIN_SECRET_TOKEN", "superadminsecret")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async session dependency with automatic rollback on error and commit/close."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_supabase_client() -> Client:
    """Returns initialized Supabase Admin Client using service role key."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials are not configured in environment variables."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validates admin bearer token. Can verify against your existing JWT auth
    or ADMIN_SECRET_TOKEN.
    """
    token = credentials.credentials
    if token != ADMIN_SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"role": "admin"}
