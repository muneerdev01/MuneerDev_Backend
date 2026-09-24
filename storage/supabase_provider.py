"""
Supabase Storage Provider
Implementation of StorageProvider for Supabase
"""
import os
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from io import BufferedReader

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None  # type: ignore

if TYPE_CHECKING:
    from supabase import Client

from security.environment import get_required_env
from storage.storage_interface import StorageProvider, StorageService


class SupabaseStorageProvider(StorageProvider):
    """
    Supabase Storage provider implementation.
    Uses Supabase storage for file operations.
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize Supabase storage provider.
        
        Args:
            supabase_url: Supabase project URL (from env if not provided)
            supabase_key: Supabase service key (from env if not provided)
        """
        if not SUPABASE_AVAILABLE:
            raise RuntimeError(
                "Supabase package not installed. Run: pip install supabase"
            )
        
        self.url = supabase_url or get_required_env("SUPABASE_URL")
        self.key = supabase_key or get_required_env("SUPABASE_SERVICE_KEY")
        self._client = None
    
    @property
    def client(self) -> "Client":  # type: ignore
        """Get or create Supabase client"""
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client
    
    async def upload_file(
        self,
        file: BufferedReader,
        bucket: str,
        file_path: str,
        metadata: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Supabase storage.
        
        Args:
            file: File object to upload
            bucket: Bucket name
            file_path: Path within bucket
            metadata: Optional file metadata
            
        Returns:
            Dict with file info (url, path, size, etc.)
        """
        try:
            # Read file content
            file_content = file.read()
            file_size = len(file_content)
            file.seek(0)  # Reset file pointer
            
            # Upload file
            response = self.client.storage.from_(bucket).upload(
                path=file_path,
                file=file,
                file_options={
                    "content-type": file.content_type if hasattr(file, 'content_type') else 'application/octet-stream',
                    "cache-control": "3600",
                    "upsert": True
                }
            )
            
            # Generate public URL
            public_url = f"{self.url}/storage/v1/object/public/{bucket}/{file_path}"
            
            return {
                "file_path": file_path,
                "url": public_url,
                "bucket": bucket,
                "size": file_size,
                "content_type": file.content_type if hasattr(file, 'content_type') else 'application/octet-stream',
                "metadata": metadata or {}
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to upload file to Supabase: {str(e)}")
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete a file from Supabase storage.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            True if deletion successful
        """
        try:
            response = self.client.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete file from Supabase: {str(e)}")
    
    async def get_public_url(self, bucket: str, file_path: str) -> Optional[str]:
        """
        Get public URL for a file.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            Public URL or None if not available
        """
        try:
            # Get public URL
            public_url = f"{self.url}/storage/v1/object/public/{bucket}/{file_path}"
            return public_url
        except Exception:
            return None
    
    async def list_files(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List files in a bucket with optional prefix.
        
        Args:
            bucket: Bucket name
            prefix: Filter by prefix
            
        Returns:
            List of file info dicts
        """
        try:
            response = self.client.storage.from_(bucket).list(
                path=prefix,
                limit=100,
                offset=0,
                search=""
            )
            
            files = []
            for file in response:
                files.append({
                    "name": file["name"],
                    "bucket_id": file.get("bucket_id", bucket),
                    "owner": file.get("owner"),
                    "updated_at": file.get("updated_at"),
                    "created_at": file.get("created_at"),
                    "last_accessed_at": file.get("last_accessed_at"),
                    "metadata": file.get("metadata", {}),
                    "size": file.get("size", 0),
                    "upload_url": file.get("upload_url"),
                    "version": file.get("version"),
                })
            
            return files
            
        except Exception as e:
            raise RuntimeError(f"Failed to list files from Supabase: {str(e)}")
    
    async def file_exists(self, bucket: str, file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            bucket: Bucket name
            file_path: Path to file
            
        Returns:
            True if file exists
        """
        try:
            response = self.client.storage.from_(bucket).list(
                path=os.path.dirname(file_path) if os.path.dirname(file_path) else ".",
                limit=100
            )
            file_names = [f["name"] for f in response]
            return os.path.basename(file_path) in file_names
        except Exception:
            return False


# Global storage service instance
storage_service = StorageService()


async def get_storage_service() -> StorageService:
    """
    Get the global storage service instance.
    Call this after setting up the provider.
    """
    if not storage_service._initialized:
        # Initialize with Supabase provider
        storage_service.set_provider(SupabaseStorageProvider())
        storage_service._initialized = True
    return storage_service


def create_supabase_storage_service() -> StorageService:
    """
    Create a new storage service with Supabase provider.
    
    Returns:
        StorageService instance configured with Supabase
    """
    service = StorageService()
    service.set_provider(SupabaseStorageProvider())
    service._initialized = True
    return service
