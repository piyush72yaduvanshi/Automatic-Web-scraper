"""Official Instagram Content Publishing API Provider."""

from typing import Dict, Any, List, Optional
import logging
import httpx

from app.core.config import settings
from app.providers.social.base import BaseSocialProvider
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class InstagramProvider(BaseSocialProvider):
    """Official Meta Instagram Graph API / Content Publishing API provider."""

    platform_name: str = "INSTAGRAM"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(settings.INSTAGRAM_ACCESS_TOKEN and settings.INSTAGRAM_BUSINESS_ACCOUNT_ID)

    @classmethod
    async def test_connection(cls) -> Dict[str, Any]:
        """Test Instagram Graph API connection."""
        if not cls.is_configured():
            return {
                "configured": False,
                "status": "NOT_CONFIGURED",
                "message": "Instagram API credentials (INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID) are not configured.",
                "account_name": "Instagram Business (Unconfigured)",
                "account_handle": "@unconfigured",
            }

        url = f"https://graph.facebook.com/v19.0/{settings.INSTAGRAM_BUSINESS_ACCOUNT_ID}"
        params = {
            "fields": "id,username,name,profile_picture_url,followers_count",
            "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    ProviderHealthService.record_success("instagram")
                    return {
                        "configured": True,
                        "status": "ACTIVE",
                        "account_name": data.get("name") or data.get("username", "Instagram Account"),
                        "account_handle": f"@{data.get('username', '')}",
                        "account_id": data.get("id"),
                        "followers_count": data.get("followers_count", 0),
                        "profile_image_url": data.get("profile_picture_url"),
                    }
                elif res.status_code in [401, 403]:
                    ProviderHealthService.record_failure("instagram", "Invalid or expired token", IntegrationStatus.INVALID_CREDENTIALS)
                    return {
                        "configured": True,
                        "status": "EXPIRED",
                        "error": "Instagram access token is invalid or expired.",
                    }
                else:
                    ProviderHealthService.record_failure("instagram", f"HTTP {res.status_code}")
                    return {
                        "configured": True,
                        "status": "ERROR",
                        "error": res.text,
                    }
        except Exception as e:
            logger.error(f"Instagram connection test error: {e}")
            ProviderHealthService.record_failure("instagram", str(e))
            return {
                "configured": True,
                "status": "ERROR",
                "error": str(e),
            }

    @classmethod
    async def publish_post(
        cls,
        caption: str,
        media_urls: Optional[List[str]] = None,
        creative_brief: Optional[Dict[str, Any]] = None,
        account_id_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish to Instagram via the 2-step Container Publishing API:
        1. POST /{ig-user-id}/media (create media container)
        2. POST /{ig-user-id}/media_publish (publish container)
        """
        if not cls.is_configured():
            logger.info("[InstagramProvider] Not configured. Post retained in NOT_CONFIGURED state.")
            return {
                "success": False,
                "provider_status": "NOT_CONFIGURED",
                "external_post_id": None,
                "external_post_url": None,
                "api_response": None,
                "error": "Instagram API credentials are not configured in .env. Retaining draft for manual publishing.",
            }

        ig_user_id = account_id_override or settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        image_url = media_urls[0] if media_urls and len(media_urls) > 0 else None
        if not image_url:
            return {
                "success": False,
                "provider_status": "FAILED",
                "external_post_id": None,
                "external_post_url": None,
                "api_response": None,
                "error": "Instagram requires at least one image/media URL for feed publishing.",
            }

        # Step 1: Create Container
        container_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        container_payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res1 = await client.post(container_url, data=container_payload)
                if res1.status_code != 200:
                    err = res1.text
                    logger.error(f"Instagram container creation failed: {err}")
                    return {
                        "success": False,
                        "provider_status": "FAILED",
                        "external_post_id": None,
                        "external_post_url": None,
                        "api_response": res1.json() if res1.headers.get("content-type", "").startswith("application/json") else {"text": err},
                        "error": f"Failed to create Instagram media container: {err}",
                    }
                
                container_id = res1.json().get("id")

                # Step 2: Publish Container
                publish_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish"
                publish_payload = {
                    "creation_id": container_id,
                    "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
                }
                res2 = await client.post(publish_url, data=publish_payload)
                if res2.status_code == 200:
                    data = res2.json()
                    media_id = data.get("id")
                    ProviderHealthService.record_success("instagram")
                    return {
                        "success": True,
                        "provider_status": "LIVE_API",
                        "external_post_id": media_id,
                        "external_post_url": f"https://www.instagram.com/p/{media_id}/",
                        "api_response": data,
                        "error": None,
                    }
                else:
                    err = res2.text
                    logger.error(f"Instagram media publish failed: {err}")
                    return {
                        "success": False,
                        "provider_status": "FAILED",
                        "external_post_id": None,
                        "external_post_url": None,
                        "api_response": res2.json() if res2.headers.get("content-type", "").startswith("application/json") else {"text": err},
                        "error": f"Instagram publish failed: {err}",
                    }
        except Exception as e:
            logger.error(f"Instagram API network error: {e}")
            return {
                "success": False,
                "provider_status": "FAILED",
                "external_post_id": None,
                "external_post_url": None,
                "api_response": None,
                "error": str(e),
            }

    @classmethod
    async def get_post_metrics(cls, external_post_id: str) -> Dict[str, Any]:
        """Query post metrics from Instagram Graph API."""
        if not cls.is_configured() or not external_post_id:
            return {
                "impressions": 0,
                "reach": 0,
                "engagement_count": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "clicks": 0,
                "engagement_rate": 0.0,
            }

        url = f"https://graph.facebook.com/v19.0/{external_post_id}/insights"
        params = {
            "metric": "impressions,reach,likes,comments,shares,saved",
            "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    metrics_raw = res.json().get("data", [])
                    res_map = {m.get("name"): m.get("values", [{}])[0].get("value", 0) for m in metrics_raw}
                    impressions = res_map.get("impressions", 0)
                    reach = res_map.get("reach", 0)
                    likes = res_map.get("likes", 0)
                    comments = res_map.get("comments", 0)
                    shares = res_map.get("shares", 0)
                    engagements = likes + comments + shares
                    rate = (engagements / max(impressions, 1)) * 100
                    return {
                        "impressions": impressions,
                        "reach": reach,
                        "engagement_count": engagements,
                        "likes": likes,
                        "comments": comments,
                        "shares": shares,
                        "clicks": 0,
                        "engagement_rate": round(rate, 2),
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch Instagram metrics: {e}")

        return {
            "impressions": 0,
            "reach": 0,
            "engagement_count": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "engagement_rate": 0.0,
        }
