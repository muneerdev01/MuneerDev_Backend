"""
SQLAlchemy 2.0 Async Model: Project
Path: models/project.py
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base, TimestampMixin

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(250), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Store list of technologies as JSON array, e.g. ["Next.js", "FastAPI", "TailwindCSS"]
    tech_stack: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Store list of image preview URLs as JSON array
    images: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Project id={self.id} title={self.title!r} slug={self.slug!r}>"
