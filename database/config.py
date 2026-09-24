"""
Database Configuration and Session Management
"""
import os
from typing import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
# Navigate up to root directory (two levels up from database/config.py)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=False)

# Database URL from environment (Supabase PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(f"DATABASE_URL environment variable is not set. Checked path: {env_path}")

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for FastAPI routes.
    Provides an async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Sync engine for migrations or background tasks
sync_engine = create_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)
