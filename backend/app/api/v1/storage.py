"""Storage & Media Asset API Endpoints backed by MinIO."""

from typing import Dict, Any, List, Optional
import os
import mimetypes
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.storage_service import MinIOStorageService

router = APIRouter(prefix="/storage", tags=["storage"])

DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".ps1", ".vbs", ".js", 
    ".php", ".pl", ".py", ".rb", ".jar", ".msi", ".dll", ".so", ".bin"
}


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
    """Upload any image, banner, or collateral asset directly to MinIO with security validation."""
    filename = file.filename or "upload"
    _, ext = os.path.splitext(filename.lower())
    if ext in DANGEROUS_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' is not permitted for enterprise security."
        )

    try:
        content = await file.read()
        content_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        result = MinIOStorageService.upload_bytes(
            data=content,
            filename=filename,
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


@router.get("/files/{object_path:path}")
def serve_local_fallback_file(object_path: str):
    """
    Serves files stored in local fallback storage or mirrors MinIO objects.
    Enforces strict path traversal mitigation and provides browser caching headers.
    """
    clean_path = os.path.normpath(object_path).replace("\\", "/")
    if clean_path.startswith("..") or "/../" in clean_path:
        raise HTTPException(status_code=400, detail="Invalid path traversal sequence detected")

    uploads_base = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
    target_path = os.path.abspath(os.path.join(uploads_base, clean_path))

    if not target_path.startswith(uploads_base):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(target_path):
        # Attempt transparent fetch from MinIO if available
        data = MinIOStorageService.download_bytes(object_name=clean_path)
        if data:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(data)
        else:
            raise HTTPException(status_code=404, detail="Asset not found")

    guess_type, _ = mimetypes.guess_type(target_path)
    return FileResponse(
        target_path,
        media_type=guess_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=86400, stale-while-revalidate=604800"}
    )
