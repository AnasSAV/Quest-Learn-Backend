from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.upload_token import UploadToken
from app.services.storage import storage_service
from app.core.config import settings

router = APIRouter()


@router.post("/presign")
async def generate_presigned_upload_url(
    content_type: str = Query(..., description="MIME type of the file to upload"),
    filename: Optional[str] = Query(None, description="Suggested filename"),
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate a presigned URL for uploading files to Supabase storage."""
    
    # Validate content type
    if content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type {content_type} not allowed. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Extract file extension from content type or filename
    file_extension = "png"
    if content_type == "image/jpeg":
        file_extension = "jpg"
    elif filename and "." in filename:
        file_extension = filename.split(".")[-1].lower()
    
    # Generate presigned URL
    try:
        upload_url, file_path = await storage_service.generate_upload_url(
            file_extension=file_extension,
            content_type=content_type,
            user_id=current_teacher.id,
            expires_in_minutes=60
        )
        
        # Store upload token in database for tracking
        upload_token = UploadToken(
            created_by=current_teacher.id,
            content_type=content_type,
            key_hint=filename or file_path,
            presigned_url=upload_url,
            expires_at=datetime.utcnow() + timedelta(minutes=60)
        )
        
        db.add(upload_token)
        await db.commit()
        await db.refresh(upload_token)
        
        # Generate public URL for the file (for later use in questions)
        public_url = await storage_service.get_public_url(file_path)
        
        return {
            "upload_url": upload_url,
            "file_path": file_path,
            "public_url": public_url,
            "expires_at": upload_token.expires_at.isoformat(),
            "upload_instructions": {
                "method": "PUT",
                "content_type": content_type,
                "max_size_mb": settings.MAX_UPLOAD_MB
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}"
        )


@router.post("/sign-download")
async def generate_presigned_download_url(
    file_path: str = Query(..., description="Path to the file in storage"),
    expires_in_minutes: int = Query(60, ge=1, le=1440, description="URL expiration in minutes"),
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Generate a presigned URL for downloading files from Supabase storage."""
    
    try:
        download_url = await storage_service.generate_download_url(
            file_path=file_path,
            expires_in_minutes=expires_in_minutes
        )
        
        return {
            "download_url": download_url,
            "expires_at": (datetime.utcnow() + timedelta(minutes=expires_in_minutes)).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.get("/public-url")
async def get_public_url(
    file_path: str = Query(..., description="Path to the file in storage"),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get the public URL for a file (if bucket is public)."""
    
    try:
        public_url = await storage_service.get_public_url(file_path)
        
        return {
            "public_url": public_url,
            "file_path": file_path
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get public URL: {str(e)}"
        )


@router.delete("/file")
async def delete_file(
    file_path: str = Query(..., description="Path to the file in storage"),
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Delete a file from Supabase storage."""
    
    # Extract the file path from URL if a full URL was provided
    extracted_path = storage_service.extract_file_path_from_url(file_path)
    if extracted_path:
        file_path = extracted_path
    
    # Check if the file belongs to the current teacher
    # This is a simple check based on the file path structure
    if not file_path.startswith(f"questions/{current_teacher.id}/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own files"
        )
    
    try:
        success = await storage_service.delete_file(file_path)
        
        if success:
            # Remove any upload tokens for this file
            from sqlalchemy import delete
            await db.execute(
                delete(UploadToken).where(
                    UploadToken.created_by == current_teacher.id,
                    UploadToken.key_hint.contains(file_path)
                )
            )
            await db.commit()
            
            return {"message": "File deleted successfully", "file_path": file_path}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/my-tokens")
async def get_my_upload_tokens(
    db: AsyncSession = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Get upload tokens created by the current teacher."""
    
    from sqlalchemy import select
    
    query = select(UploadToken).where(
        UploadToken.created_by == current_teacher.id
    ).order_by(UploadToken.created_at.desc()).limit(50)
    
    result = await db.execute(query)
    tokens = result.scalars().all()
    
    return [
        {
            "id": token.id,
            "content_type": token.content_type,
            "key_hint": token.key_hint,
            "expires_at": token.expires_at.isoformat(),
            "created_at": token.created_at.isoformat(),
            "is_expired": token.is_expired
        }
        for token in tokens
    ]
