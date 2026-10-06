"""
FastAPI Router: Projects
Path: app/api/v1/projects.py
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin
from app.models.project import Project
from app.schemas.project import ProjectRead, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("", response_model=List[ProjectRead])
async def list_projects(
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint: Get all portfolio projects ordered by featured status then creation date.
    """
    stmt = (
        select(Project)
        .order_by(Project.featured.desc(), Project.created_at.desc())
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()
    return projects

@router.get("/{slug}", response_model=ProjectRead)
async def get_project_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint: Retrieve single project by its unique slug.
    """
    stmt = select(Project).where(Project.slug == slug)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with slug '{slug}' not found"
        )
    return project

@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin)
):
    """
    Admin only: Create new portfolio project.
    """
    # Verify slug uniqueness
    stmt = select(Project).where(Project.slug == payload.slug)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with slug '{payload.slug}' already exists."
        )

    project = Project(**payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project

@router.put("/{slug}", response_model=ProjectRead)
async def update_project(
    slug: str,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin)
):
    """
    Admin only: Update existing portfolio project.
    """
    stmt = select(Project).where(Project.slug == slug)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with slug '{slug}' not found"
        )

    update_data = payload.model_dump(exclude_unset=True)
    
    # If slug is being updated, verify new slug isn't taken
    if "slug" in update_data and update_data["slug"] != slug:
        check_stmt = select(Project).where(Project.slug == update_data["slug"])
        existing_check = await db.execute(check_stmt)
        if existing_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project slug '{update_data['slug']}' is already in use."
            )

    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(get_current_admin)
):
    """
    Admin only: Permanently delete project by slug.
    """
    stmt = select(Project).where(Project.slug == slug)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with slug '{slug}' not found"
        )

    await db.delete(project)
    await db.commit()
    return None
