"""Official Facebook Pages Graph API Provider."""

from typing import Dict, Any, List, Optional
import logging
import httpx

from app.core.config import settings
from app.providers.social.base import BaseSocialProvider
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class FacebookProvider(BaseSocialProvider):
    """Official Facebook Pages Graph API provider."""

    platform_name: str = "FACEBOOK"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(settings.FACEBOOK_PAGE_ACCESS_TOKEN and settings.FACEBOOK_PAGE_ID)

    @classmethod
    async def test_connection(cls) -> Dict[str, Any]:
        """Verify Facebook Page access token and fetch page metadata."""
        if not cls.is_configured():
            return {
                "configured": False,
                "status": "NOT_CONFIGURED",
                "message": "Facebook Page credentials (FACEBOOK_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID) are not configured.",
                "account_name": "Facebook Page (Unconfigured)",
                "account_handle": "fb.com/unconfigured",
            }

        url = f"https://graph.facebook.com/v19.0/{settings.FACEBOOK_PAGE_ID}"
        params = {
            "fields": "id,name,link,picture,fan_count",
            "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    ProviderHealthService.record_success("facebook")
                    return {
                        "configured": True,
                        "status": "ACTIVE",
                        "account_name": data.get("name", "Facebook Page"),
                        "account_handle": data.get("link", f"facebook.com/{settings.FACEBOOK_PAGE_ID}"),
                        "account_id": data.get("id"),
                        "followers_count": data.get("fan_count", 0),
                        "profile_image_url": data.get("picture", {}).get("data", {}).get("url"),
                    }
                elif res.status_code in [401, 403]:
                    ProviderHealthService.record_failure("facebook", "Invalid or expired page token", IntegrationStatus.INVALID_CREDENTIALS)
                    return {
                        "configured": True,
                        "status": "EXPIRED",
                        "error": "Facebook Page access token is invalid or expired.",
                    }
                else:
                    ProviderHealthService.record_failure("facebook", f"HTTP {res.status_code}")
                    return {
                        "configured": True,
                        "status": "ERROR",
                        "error": res.text,
                    }
        except Exception as e:
            logger.error(f"Facebook connection test error: {e}")
            ProviderHealthService.record_failure("facebook", str(e))
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
        """Publish post or photo to Facebook Page Feed."""
        if not cls.is_configured():
            logger.info("[FacebookProvider] Not configured. Post retained in NOT_CONFIGURED state.")
            return {
                "success": False,
                "provider_status": "NOT_CONFIGURED",
                "external_post_id": None,
                "external_post_url": None,
                "api_response": None,
                "error": "Facebook Page credentials are not configured in .env. Retaining draft for manual publishing.",
            }

        page_id = account_id_override or settings.FACEBOOK_PAGE_ID
        image_url = media_urls[0] if media_urls and len(media_urls) > 0 else None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if image_url:
                    # Publish Photo Post
                    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                    payload = {
                        "url": image_url,
                        "caption": caption,
                        "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN,
                    }
                else:
                    # Publish Status Post
                    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
                    payload = {
                        "message": caption,
                        "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN,
                    }

                res = await client.post(url, data=payload)
                if res.status_code == 200:
                    data = res.json()
                    post_id = data.get("id") or data.get("post_id")
                    ProviderHealthService.record_success("facebook")
                    return {
                        "success": True,
                        "provider_status": "LIVE_API",
                        "external_post_id": post_id,
                        "external_post_url": f"https://facebook.com/{post_id}",
                        "api_response": data,
                        "error": None,
                    }
                else:
                    err = res.text
                    logger.error(f"Facebook publish failed: {err}")
                    return {
                        "success": False,
                        "provider_status": "FAILED",
                        "external_post_id": None,
                        "external_post_url": None,
                        "api_response": res.json() if res.headers.get("content-type", "").startswith("application/json") else {"text": err},
                        "error": f"Facebook post failed: {err}",
                    }
        except Exception as e:
            logger.error(f"Facebook API network error: {e}")
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
        """Fetch post impressions and reactions from Facebook Graph API."""
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
            "metric": "post_impressions,post_engaged_users,post_reactions_by_type_total",
            "access_token": settings.FACEBOOK_PAGE_ACCESS_TOKEN,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    metrics_raw = res.json().get("data", [])
                    res_map = {m.get("name"): m.get("values", [{}])[0].get("value", 0) for m in metrics_raw}
                    impressions = res_map.get("post_impressions", 0)
                    engagements = res_map.get("post_engaged_users", 0)
                    reactions = res_map.get("post_reactions_by_type_total", {})
                    likes = reactions.get("like", 0) if isinstance(reactions, dict) else 0
                    rate = (engagements / max(impressions, 1)) * 100
                    return {
                        "impressions": impressions,
                        "reach": impressions,
                        "engagement_count": engagements,
                        "likes": likes,
                        "comments": 0,
                        "shares": 0,
                        "clicks": 0,
                        "engagement_rate": round(rate, 2),
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch Facebook metrics: {e}")

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
