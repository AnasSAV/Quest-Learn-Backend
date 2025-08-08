import uuid
from datetime import datetime, timedelta
from typing import Optional
from supabase import create_client, Client
from fastapi import HTTPException, status

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET

    async def generate_upload_url(
        self,
        file_extension: str,
        content_type: str,
        user_id: int,
        expires_in_minutes: int = 60
    ) -> tuple[str, str]:
        """
        Generate a presigned URL for uploading files to Supabase storage.
        
        Returns:
            tuple: (upload_url, file_path)
        """
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content type {content_type} not allowed"
            )

        # Generate unique filename
        unique_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = f"questions/{user_id}/{timestamp}_{unique_id}.{file_extension}"

        try:
            # Create presigned URL for upload
            response = self.supabase.storage.from_(self.bucket_name).create_signed_upload_url(file_path)
            
            if not response.get('signedURL'):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate upload URL"
                )
            
            return response['signedURL'], file_path
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage service error: {str(e)}"
            )

    async def generate_download_url(
        self,
        file_path: str,
        expires_in_minutes: int = 60
    ) -> str:
        """
        Generate a presigned URL for downloading files from Supabase storage.
        """
        try:
            response = self.supabase.storage.from_(self.bucket_name).create_signed_url(
                file_path, 
                expires_in=expires_in_minutes * 60
            )
            
            if not response.get('signedURL'):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate download URL"
                )
            
            return response['signedURL']
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage service error: {str(e)}"
            )

    async def get_public_url(self, file_path: str) -> str:
        """
        Get the public URL for a file in Supabase storage.
        Note: This only works if the bucket is public.
        """
        try:
            response = self.supabase.storage.from_(self.bucket_name).get_public_url(file_path)
            return response['publicURL']
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage service error: {str(e)}"
            )

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Supabase storage.
        """
        try:
            response = self.supabase.storage.from_(self.bucket_name).remove([file_path])
            return len(response) > 0
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage service error: {str(e)}"
            )

    def validate_file_size(self, file_size: int) -> bool:
        """
        Validate if file size is within allowed limits.
        """
        return file_size <= settings.max_upload_bytes

    def extract_file_path_from_url(self, url: str) -> Optional[str]:
        """
        Extract the file path from a Supabase storage URL.
        """
        try:
            # Supabase public URL format: https://project.supabase.co/storage/v1/object/public/bucket/path
            parts = url.split('/storage/v1/object/public/')
            if len(parts) == 2:
                bucket_and_path = parts[1]
                path_parts = bucket_and_path.split('/', 1)
                if len(path_parts) == 2 and path_parts[0] == self.bucket_name:
                    return path_parts[1]
            return None
        except Exception:
            return None


# Global storage service instance
storage_service = StorageService()
