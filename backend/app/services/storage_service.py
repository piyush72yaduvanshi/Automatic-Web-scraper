"""MinIO High-Performance S3-Compatible Object Storage Service.

Manages persistent storage for images, creative assets, social media banners,
lead collateral, and generated export files using MinIO with automatic local fallback.
"""

import io
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, BinaryIO
from urllib.parse import urljoin

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_LIB_AVAILABLE = True
except ImportError:
    MINIO_LIB_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOStorageService:
    """Enterprise Object Storage Service powered by MinIO."""

    _client: Optional[Any] = None
    _client_initialized: bool = False
    _bucket_verified: bool = False
    _fallback_dir: str = os.path.join(os.getcwd(), "uploads")

    @classmethod
    def get_client(cls) -> Optional[Any]:
        """Lazy-initialize MinIO S3 client."""
        if not MINIO_LIB_AVAILABLE:
            return None

        if cls._client is None and not cls._client_initialized:
            cls._client_initialized = True
            try:
                # Strip protocol if present in endpoint
                endpoint = settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", "").rstrip("/")
                cls._client = Minio(
                    endpoint=endpoint,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE,
                )
                logger.info(f"Initialized MinIO client connected to {endpoint}")
            except Exception as e:
                logger.warning(f"Failed to initialize MinIO client: {e}. Local fallback will be used.")
                cls._client = None

        return cls._client

    @classmethod
    def is_available(cls) -> bool:
        """Check if MinIO server is reachable."""
        client = cls.get_client()
        if not client:
            return False
        try:
            # Simple probe
            client.list_buckets()
            return True
        except Exception as e:
            logger.debug(f"MinIO health check probe failed: {e}")
            return False

    @classmethod
    def ensure_bucket_exists(cls, bucket_name: Optional[str] = None) -> bool:
        """Verify bucket existence; auto-create if missing."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        client = cls.get_client()
        if not client:
            return False

        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info(f"MinIO bucket '{bucket}' created successfully.")

                # Set anonymous read policy for public assets if desirable
                try:
                    import json
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": ["*"]},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{bucket}/*"],
                            }
                        ],
                    }
                    client.set_bucket_policy(bucket, json.dumps(policy))
                except Exception as pe:
                    logger.debug(f"Bucket public policy set skipped: {pe}")

            cls._bucket_verified = True
            return True
        except Exception as e:
            logger.warning(f"Error ensuring MinIO bucket '{bucket}': {e}")
            return False

    @classmethod
    def upload_bytes(
        cls,
        data: bytes,
        filename: str,
        content_type: str = "image/png",
        bucket_name: Optional[str] = None,
        folder: str = "images",
    ) -> Dict[str, Any]:
        """
        Upload binary data (image, document, asset) to MinIO.
        Returns persistent public URL, key, and metadata.
        Falls back seamlessly to local disk if MinIO is offline.
        """
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        clean_filename = os.path.basename(filename).replace(" ", "_")
        unique_prefix = uuid.uuid4().hex[:10]
        object_name = f"{folder}/{unique_prefix}_{clean_filename}"

        client = cls.get_client()
        if client and cls.ensure_bucket_exists(bucket):
            try:
                stream = io.BytesIO(data)
                client.put_object(
                    bucket_name=bucket,
                    object_name=object_name,
                    data=stream,
                    length=len(data),
                    content_type=content_type,
                )

                base_public_url = (settings.MINIO_PUBLIC_URL or f"http://{settings.MINIO_ENDPOINT}").rstrip("/")
                public_url = f"{base_public_url}/{bucket}/{object_name}"

                logger.info(f"Uploaded asset to MinIO: {object_name} ({len(data)} bytes)")
                return {
                    "storage_provider": "minio",
                    "bucket": bucket,
                    "object_name": object_name,
                    "url": public_url,
                    "content_type": content_type,
                    "size_bytes": len(data),
                    "created_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.warning(f"MinIO put_object failed ({e}). Falling back to local storage.")

        # Local storage fallback
        return cls._store_local_fallback(data, object_name, content_type)

    @classmethod
    def _store_local_fallback(cls, data: bytes, object_name: str, content_type: str) -> Dict[str, Any]:
        """Save file locally when MinIO is not running or during local tests."""
        dest_path = os.path.join(cls._fallback_dir, object_name)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)

        local_url = f"http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/api/v1/storage/files/{object_name}"
        return {
            "storage_provider": "local_fallback",
            "bucket": "local",
            "object_name": object_name,
            "url": local_url,
            "local_path": dest_path,
            "content_type": content_type,
            "size_bytes": len(data),
            "created_at": datetime.utcnow().isoformat(),
        }

    @classmethod
    def download_bytes(cls, object_name: str, bucket_name: Optional[str] = None) -> Optional[bytes]:
        """Retrieve binary data from MinIO or local fallback."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        client = cls.get_client()
        if client:
            try:
                response = client.get_object(bucket, object_name)
                try:
                    return response.read()
                finally:
                    response.close()
                    response.release_conn()
            except Exception as e:
                logger.debug(f"MinIO get_object failed: {e}")

        # Try local fallback
        dest_path = os.path.join(cls._fallback_dir, object_name)
        if os.path.exists(dest_path):
            with open(dest_path, "rb") as f:
                return f.read()

        return None

    @classmethod
    def get_presigned_url(
        cls,
        object_name: str,
        bucket_name: Optional[str] = None,
        expires_seconds: int = 3600,
    ) -> str:
        """Generate a time-limited pre-signed download/view URL."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        client = cls.get_client()
        if client:
            try:
                return client.presigned_get_object(
                    bucket_name=bucket,
                    object_name=object_name,
                    expires=timedelta(seconds=expires_seconds),
                )
            except Exception as e:
                logger.warning(f"Failed to generate pre-signed URL: {e}")

        # Fallback to direct public URL
        base_public_url = (settings.MINIO_PUBLIC_URL or f"http://{settings.MINIO_ENDPOINT}").rstrip("/")
        return f"{base_public_url}/{bucket}/{object_name}"

    @classmethod
    def delete_object(cls, object_name: str, bucket_name: Optional[str] = None) -> bool:
        """Delete an object from MinIO."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        client = cls.get_client()
        deleted = False
        if client:
            try:
                client.remove_object(bucket, object_name)
                deleted = True
            except Exception as e:
                logger.warning(f"Error removing MinIO object '{object_name}': {e}")

        # Remove local file if present
        local_path = os.path.join(cls._fallback_dir, object_name)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                deleted = True
            except Exception:
                pass

        return deleted

    @classmethod
    def list_objects(
        cls,
        prefix: str = "",
        bucket_name: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List stored assets in MinIO bucket."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        client = cls.get_client()
        items = []

        if client and cls.ensure_bucket_exists(bucket):
            try:
                objs = client.list_objects(bucket, prefix=prefix, recursive=True)
                for o in objs:
                    items.append({
                        "object_name": o.object_name,
                        "size": o.size,
                        "last_modified": o.last_modified.isoformat() if o.last_modified else None,
                        "url": f"{(settings.MINIO_PUBLIC_URL or f'http://{settings.MINIO_ENDPOINT}').rstrip('/')}/{bucket}/{o.object_name}",
                    })
                    if len(items) >= limit:
                        break
                return items
            except Exception as e:
                logger.warning(f"Error listing MinIO objects: {e}")

        # List local fallback files
        base_dir = os.path.join(cls._fallback_dir, prefix)
        if os.path.exists(base_dir):
            for root, _, files in os.walk(base_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, cls._fallback_dir).replace("\\", "/")
                    items.append({
                        "object_name": rel_p,
                        "size": os.path.getsize(full_p),
                        "last_modified": datetime.fromtimestamp(os.path.getmtime(full_p)).isoformat(),
                        "url": f"http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/api/v1/storage/files/{rel_p}",
                    })
                    if len(items) >= limit:
                        break

        return items

    @classmethod
    def generate_and_store_creative_image(
        cls,
        title: str,
        text_overlay: str,
        platform: str = "INSTAGRAM",
        style: str = "modern_gradient",
    ) -> Dict[str, Any]:
        """
        Generates a high-resolution branded creative banner and uploads directly to MinIO.
        Produces SVG graphics tailored to the platform aspect ratio (1080x1080 for Instagram, 1200x630 for LinkedIn/Facebook, 1200x675 for X).
        """
        # Select dimensions
        platform_upper = platform.upper()
        if platform_upper in ["INSTAGRAM", "INSTAGRAM_SQUARE"]:
            width, height = 1080, 1080
        elif platform_upper in ["X", "TWITTER"]:
            width, height = 1200, 675
        else:  # LINKEDIN, FACEBOOK
            width, height = 1200, 630

        # Design palettes
        palettes = {
            "modern_gradient": ("#4f46e5", "#06b6d4", "#0f172a"),
            "executive_dark": ("#1e293b", "#3b82f6", "#020617"),
            "growth_emerald": ("#059669", "#10b981", "#064e3b"),
            "vibrant_purple": ("#7c3aed", "#ec4899", "#18181b"),
        }
        color_start, color_mid, color_bg = palettes.get(style, palettes["modern_gradient"])

        clean_title = (title or "AI Sales & Growth").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        clean_text = (text_overlay or "Accelerate your revenue engine").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Render high-res modern SVG banner
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{color_start}"/>
      <stop offset="50%" stop-color="{color_mid}"/>
      <stop offset="100%" stop-color="{color_bg}"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.05"/>
    </linearGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="16" stdDeviation="24" flood-color="#000000" flood-opacity="0.4"/>
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad)"/>

  <!-- Geometric Accent Circles -->
  <circle cx="{width * 0.9}" cy="{height * 0.15}" r="{width * 0.25}" fill="#ffffff" fill-opacity="0.08"/>
  <circle cx="{width * 0.1}" cy="{height * 0.85}" r="{width * 0.2}" fill="#ffffff" fill-opacity="0.05"/>

  <!-- Central Glassmorphism Card -->
  <rect x="{width * 0.08}" y="{height * 0.12}" width="{width * 0.84}" height="{height * 0.76}" rx="32" fill="url(#cardGrad)" stroke="#ffffff" stroke-opacity="0.25" stroke-width="2" filter="url(#cardShadow)"/>

  <!-- Platform Badge -->
  <rect x="{width * 0.14}" y="{height * 0.22}" width="180" height="42" rx="21" fill="#ffffff" fill-opacity="0.2"/>
  <text x="{width * 0.14 + 90}" y="{height * 0.22 + 27}" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="700" fill="#ffffff" text-anchor="middle" letter-spacing="1.5">{platform_upper}</text>

  <!-- Title / Category Header -->
  <text x="{width * 0.14}" y="{height * 0.38}" font-family="system-ui, -apple-system, sans-serif" font-size="{36 if width > 1100 else 32}" font-weight="600" fill="#e0e7ff" opacity="0.9">{clean_title[:60]}</text>

  <!-- Headline Text Overlay -->
  <text x="{width * 0.14}" y="{height * 0.52}" font-family="system-ui, -apple-system, sans-serif" font-size="{52 if width > 1100 else 44}" font-weight="800" fill="#ffffff" width="{width * 0.72}">
    <tspan x="{width * 0.14}" dy="0">{clean_text[:50]}</tspan>
    {f'<tspan x="{width * 0.14}" dy="64">{clean_text[50:110]}</tspan>' if len(clean_text) > 50 else ''}
  </text>

  <!-- Branding & Verification Footer -->
  <line x1="{width * 0.14}" y1="{height * 0.76}" x2="{width * 0.86}" y2="{height * 0.76}" stroke="#ffffff" stroke-opacity="0.2" stroke-width="1.5"/>
  <text x="{width * 0.14}" y="{height * 0.82}" font-family="system-ui, -apple-system, sans-serif" font-size="20" font-weight="600" fill="#ffffff" opacity="0.85">AI Sales &amp; CRM Operating System</text>
  <text x="{width * 0.86}" y="{height * 0.82}" font-family="system-ui, -apple-system, sans-serif" font-size="18" font-weight="500" fill="#cbd5e1" text-anchor="end">MinIO Object Store Verified</text>
</svg>"""

        svg_bytes = svg_content.encode("utf-8")
        filename = f"creative_{platform.lower()}_{uuid.uuid4().hex[:8]}.svg"

        # Upload generated banner to MinIO
        upload_res = cls.upload_bytes(
            data=svg_bytes,
            filename=filename,
            content_type="image/svg+xml",
            folder="creatives",
        )

        return {
            "image_url": upload_res["url"],
            "object_name": upload_res["object_name"],
            "platform": platform_upper,
            "style": style,
            "width": width,
            "height": height,
            "size_bytes": len(svg_bytes),
            "storage_provider": upload_res.get("storage_provider", "minio"),
        }

