"""
Storage Abstraction Interface
Provider-agnostic storage operations
"""
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from io import BufferedReader


class StorageProvider(ABC):
    """
    Abstract base class for storage providers.
    All storage providers must implement these methods.
    """
    
    @abstractmethod
    async def upload_file(
        self,
        file: BufferedReader,
        bucket: str,
        file_path: str,
        metadata: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to storage.
        
        Args:
            file: File object to upload
            bucket: Bucket name
            file_path: Path within bucket
            metadata: Optional file metadata
            
        Returns:
            Dict with file info (url, path, size, etc.)
        """
        pass
    
    @abstractmethod
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            True if deletion successful
        """
        pass
    
    @abstractmethod
    async def get_public_url(self, bucket: str, file_path: str) -> Optional[str]:
        """
        Get public URL for a file.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            Public URL or None if not available
        """
        pass
    
    @abstractmethod
    async def list_files(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List files in a bucket with optional prefix.
        
        Args:
            bucket: Bucket name
            prefix: Filter by prefix
            
        Returns:
            List of file info dicts
        """
        pass
    
    @abstractmethod
    async def file_exists(self, bucket: str, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            True if file exists
        """
        pass


class StorageService:
    """
    Provider-agnostic storage service.
    Wraps any storage provider implementation.
    """
    
    def __init__(self, provider: StorageProvider = None):
        """
        Initialize storage service.
        
        Args:
            provider: Storage provider instance (e.g., SupabaseStorageProvider)
        """
        self._provider = provider
        self._initialized = False
    
    async def initialize(self):
        """Initialize storage provider (if needed)"""
        # Provider-specific initialization happens in provider's __init__
        self._initialized = True
    
    def set_provider(self, provider: StorageProvider):
        """Set the storage provider"""
        self._provider = provider
    
    async def upload_file(
        self,
        file: BufferedReader,
        bucket: str,
        file_path: str,
        metadata: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to storage.
        
        Args:
            file: File object to upload
            bucket: Bucket name
            file_path: Path within bucket
            metadata: Optional file metadata
            
        Returns:
            Dict with file info (url, path, size, etc.)
        """
        if not self._provider:
            raise RuntimeError("Storage provider not initialized")
        
        return await self._provider.upload_file(file, bucket, file_path, metadata)
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            True if deletion successful
        """
        if not self._provider:
            raise RuntimeError("Storage provider not initialized")
        
        return await self._provider.delete_file(bucket, file_path)
    
    async def get_public_url(self, bucket: str, file_path: str) -> Optional[str]:
        """
        Get public URL for a file.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            Public URL or None if not available
        """
        if not self._provider:
            raise RuntimeError("Storage provider not initialized")
        
        return await self._provider.get_public_url(bucket, file_path)
    
    async def list_files(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List files in a bucket with optional prefix.
        
        Args:
            bucket: Bucket name
            prefix: Filter by prefix
            
        Returns:
            List of file info dicts
        """
        if not self._provider:
            raise RuntimeError("Storage provider not initialized")
        
        return await self._provider.list_files(bucket, prefix)
    
    async def file_exists(self, bucket: str, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            True if file exists
        """
        if not self._provider:
            raise RuntimeError("Storage provider not initialized")
        
        return await self._provider.file_exists(bucket, file_path)
