"""
Database Verification Script
Tests database connection and model imports
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_db, engine
from models.enums import BlogType, ArticleStatus, ContentFormat, EntityType
from models.category import Category
from models.tag import Tag
from models.article import Article
from models.article_tag import ArticleTag
from models.content_relationship import ContentRelationship
from models.media_asset import MediaAsset
from models.audit_log import AuditLog


async def test_connection():
    """Test database connection"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✓ Database connection successful")
                return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    return False


async def test_enums():
    """Test enum imports"""
    try:
        # Check if enums are properly defined
        assert hasattr(BlogType, "TECH"), "BlogType.TECH not found"
        assert hasattr(BlogType, "HEALTHCARE"), "BlogType.HEALTHCARE not found"
        assert hasattr(ArticleStatus, "DRAFT"), "ArticleStatus.DRAFT not found"
        assert hasattr(ArticleStatus, "PUBLISHED"), "ArticleStatus.PUBLISHED not found"
        assert hasattr(ArticleStatus, "ARCHIVED"), "ArticleStatus.ARCHIVED not found"
        assert hasattr(ContentFormat, "markdown"), "ContentFormat.markdown not found"
        assert hasattr(ContentFormat, "html"), "ContentFormat.html not found"
        assert hasattr(ContentFormat, "rich_text"), "ContentFormat.rich_text not found"
        assert hasattr(EntityType, "article"), "EntityType.article not found"
        assert hasattr(EntityType, "project"), "EntityType.project not found"
        assert hasattr(EntityType, "service"), "EntityType.service not found"
        assert hasattr(EntityType, "resource"), "EntityType.resource not found"
        assert hasattr(EntityType, "product"), "EntityType.product not found"
        assert hasattr(EntityType, "customer"), "EntityType.customer not found"
        assert hasattr(EntityType, "lead"), "EntityType.lead not found"
        print("✓ All enums imported successfully")
        return True
    except AssertionError as e:
        print(f"✗ Enum test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Enum test error: {e}")
        return False


async def test_models():
    """Test model imports and table names"""
    try:
        models = [
            (Category, "categories"),
            (Tag, "tags"),
            (Article, "articles"),
            (ArticleTag, "article_tags"),
            (ContentRelationship, "content_relationships"),
            (MediaAsset, "media_assets"),
            (AuditLog, "audit_logs"),
        ]

        for model, expected_table in models:
            assert model.__tablename__ == expected_table, f"{model.__name__} table mismatch"
            print(f"✓ {model.__name__} model loaded (table: {expected_table})")

        return True
    except AssertionError as e:
        print(f"✗ Model test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Model test error: {e}")
        return False


async def test_models_have_id():
    """Test that all models have UUID id column"""
    try:
        models = [Category, Tag, Article, ArticleTag, ContentRelationship, MediaAsset, AuditLog]
        for model in models:
            assert hasattr(model, "id"), f"{model.__name__} missing id column"
        print("✓ All models have UUID id column")
        return True
    except AssertionError as e:
        print(f"✗ ID column test failed: {e}")
        return False


async def test_timestamps():
    """Test that models have timestamps"""
    try:
        models_with_timestamps = [Category, Tag, Article, ArticleTag, ContentRelationship, MediaAsset, AuditLog]
        for model in models_with_timestamps:
            assert hasattr(model, "created_at"), f"{model.__name__} missing created_at"
            assert hasattr(model, "updated_at"), f"{model.__name__} missing updated_at"
        print("✓ All models have timestamp columns")
        return True
    except AssertionError as e:
        print(f"✗ Timestamp test failed: {e}")
        return False


async def main():
    print("=" * 50)
    print("Database Setup Verification")
    print("=" * 50)

    # Check DATABASE_URL
    if not os.getenv("DATABASE_URL"):
        print("⚠ DATABASE_URL not set. Set it in your environment.")
        print("  Example: set DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db")
        print()

    results = []

    # Test connection
    print("\n1. Testing Database Connection...")
    results.append(await test_connection())

    print("\n2. Testing Enum Imports...")
    results.append(await test_enums())

    print("\n3. Testing Model Imports...")
    results.append(await test_models())

    print("\n4. Testing UUID ID Columns...")
    results.append(await test_models_have_id())

    print("\n5. Testing Timestamp Columns...")
    results.append(await test_timestamps())

    print("\n" + "=" * 50)
    if all(results):
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed. Check output above.")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
