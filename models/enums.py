"""
SQLAlchemy Enums Definition
"""
from enum import Enum as PyEnum
from sqlalchemy import Enum

# Python Enums (for application logic)
class BlogTypeEnum(PyEnum):
    TECH = "TECH"
    HEALTHCARE = "HEALTHCARE"

class ArticleStatusEnum(PyEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class ContentFormatEnum(PyEnum):
    markdown = "markdown"
    html = "html"
    rich_text = "rich_text"

class EntityTypeEnum(PyEnum):
    article = "article"
    project = "project"
    service = "service"
    resource = "resource"
    product = "product"
    customer = "customer"
    lead = "lead"

# SQLAlchemy Enums (for database columns)
BlogType = Enum(BlogTypeEnum, name="blog_type")
ArticleStatus = Enum(ArticleStatusEnum, name="article_status")
ContentFormat = Enum(ContentFormatEnum, name="content_format")
EntityType = Enum(EntityTypeEnum, name="entity_type")
