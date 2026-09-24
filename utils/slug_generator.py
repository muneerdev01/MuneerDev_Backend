"""
Slug Generation Utility
Auto-generate unique URL-friendly slugs from title with collision prevention
"""
import re
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text.
    Removes special characters, converts to lowercase, replaces spaces with hyphens.
    """
    if not text:
        return ""
    
    # Convert to lowercase
    slug = text.lower()
    
    # Remove special characters and replace with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Collapse multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    return slug


def generate_unique_hash(length: int = 6) -> str:
    """Generate a short random hash for collision prevention"""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


async def check_slug_exists(session: AsyncSession, table, slug: str, exclude_id: str = None) -> bool:
    """
    Check if a slug already exists in the database.
    Optionally exclude a specific ID (for updates).
    """
    query = select(table).where(table.slug == slug)
    
    if exclude_id:
        query = query.where(table.id != exclude_id)
    
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


async def generate_unique_slug(
    session: AsyncSession,
    table,
    title: str,
    id_field: str = "id",
    exclude_id: str = None
) -> str:
    """
    Generate a unique slug with collision prevention.
    Appends short hash if slug already exists.
    """
    base_slug = generate_slug(title)
    slug = base_slug
    counter = 1
    
    # Keep generating until unique
    while await check_slug_exists(session, table, slug, exclude_id):
        hash_part = generate_unique_hash(4)
        slug = f"{base_slug}-{hash_part}"
        counter += 1
        
        # Safety limit
        if counter > 100:
            break
    
    return slug
