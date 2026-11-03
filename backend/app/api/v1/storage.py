"""Storage & Media Asset API Endpoints backed by MinIO."""

from typing import Dict, Any, List, Optional
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.storage_service import MinIOStorageService

router = APIRouter(prefix="/storage", tags=["storage"])


class GenerateCreativeRequest(BaseModel):
    title: str
    text_overlay: str
    platform: str = "INSTAGRAM"
    style: str = "modern_gradient"


@router.get("/status")
def get_storage_status() -> Dict[str, Any]:
    """Check health and connectivity of MinIO Object Storage."""
    available = MinIOStorageService.is_available()
    return {
        "storage_provider": "MinIO",
        "is_available": available,
        "bucket_configured": MinIOStorageService.ensure_bucket_exists() if available else False,
        "fallback_enabled": True,
    }


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Form("images"),
    bucket: Optional[str] = Form(None),
) -> Dict[str, Any]:
    """Upload any image, banner, or collateral asset directly to MinIO."""
    try:
        content = await file.read()
        content_type = file.content_type or "application/octet-stream"

        result = MinIOStorageService.upload_bytes(
            data=content,
            filename=file.filename or "upload.bin",
            content_type=content_type,
            bucket_name=bucket,
            folder=folder,
        )
        return {
            "success": True,
            "file": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload asset to storage: {str(e)}")


@router.post("/generate-creative")
def generate_creative(req: GenerateCreativeRequest) -> Dict[str, Any]:
    """Generate high-resolution social banner graphic and store directly in MinIO."""
    try:
        result = MinIOStorageService.generate_and_store_creative_image(
            title=req.title,
            text_overlay=req.text_overlay,
            platform=req.platform,
            style=req.style,
        )
        return {
            "success": True,
            "creative": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate creative: {str(e)}")


@router.get("/list")
def list_assets(
    prefix: str = Query("", description="Folder prefix e.g. images/ or creatives/"),
    limit: int = Query(50, ge=1, le=200),
) -> List[Dict[str, Any]]:
    """List assets stored in MinIO."""
    return MinIOStorageService.list_objects(prefix=prefix, limit=limit)


@router.get("/presigned-url")
def get_presigned_download_url(
    object_name: str = Query(..., description="MinIO object key"),
    expires: int = Query(3600, ge=60, le=86400),
) -> Dict[str, Any]:
    """Generate a secure pre-signed download/view URL."""
    url = MinIOStorageService.get_presigned_url(object_name=object_name, expires_seconds=expires)
    return {"object_name": object_name, "presigned_url": url}


@router.delete("/delete")
def delete_asset(object_name: str = Query(...)) -> Dict[str, Any]:
    """Delete an asset from MinIO."""
    deleted = MinIOStorageService.delete_object(object_name=object_name)
    return {"success": deleted, "object_name": object_name}


@router.get("/files/{folder}/{filename}")
def serve_local_fallback_file(folder: str, filename: str):
    """Serves files stored in local fallback storage when MinIO is in standalone/offline mode."""
    fallback_dir = os.path.join(os.getcwd(), "uploads", folder, filename)
    if not os.path.exists(fallback_dir):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(fallback_dir)

