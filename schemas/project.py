"""
Pydantic v2 Schemas: Project
Path: app/schemas/project.py
"""
import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200, example="E-Commerce Pattern Engine")
    slug: str = Field(..., min_length=2, max_length=250, example="e-commerce-pattern-engine")
    description: str = Field(..., min_length=10, example="Full-stack digital goods platform with Stripe checkout.")
    tech_stack: List[str] = Field(default_factory=list, example=["FastAPI", "PostgreSQL", "Next.js", "Tailwind"])
    images: List[str] = Field(default_factory=list, example=["https://cdn.example.com/project-preview.webp"])
    github_url: Optional[str] = Field(None, example="https://github.com/developer/portfolio-shop")
    live_url: Optional[str] = Field(None, example="https://patterns.example.com")
    featured: bool = Field(default=False)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", cleaned):
            raise ValueError("Slug must contain only lowercase alphanumeric characters and hyphens (e.g. 'my-project-name')")
        return cleaned

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    slug: Optional[str] = Field(None, min_length=2, max_length=250)
    description: Optional[str] = Field(None, min_length=10)
    tech_stack: Optional[List[str]] = None
    images: Optional[List[str]] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    featured: Optional[bool] = None

class ProjectRead(ProjectBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
