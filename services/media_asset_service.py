"""
MediaAsset Service
CRUD operations for media assets
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import MediaAsset
from services.base_service import BaseService


class MediaAssetService(BaseService[MediaAsset]):
    """Service for media asset CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(MediaAsset, session)
    
    async def get_by_url(self, url: str) -> Optional[MediaAsset]:
        """Get media asset by URL"""
        result = await self.session.execute(
            select(MediaAsset).where(MediaAsset.url == url)
        )
        return result.scalar_one_or_none()
    
    async def get_by_mime_type(self, mime_type: str) -> List[MediaAsset]:
        """Get media assets by MIME type"""
        result = await self.session.execute(
            select(MediaAsset).where(MediaAsset.mime_type == mime_type)
        )
        return result.scalars().all()
    
    async def list_by_size_range(
        self,
        min_size: int,
        max_size: int
    ) -> List[MediaAsset]:
        """Get media assets within size range"""
        result = await self.session.execute(
            select(MediaAsset)
            .where(
                MediaAsset.size_bytes >= min_size,
                MediaAsset.size_bytes <= max_size
            )
        )
        return result.scalars().all()
