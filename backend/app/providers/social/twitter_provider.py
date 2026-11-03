"""Official X (Twitter) API v2 Provider."""

from typing import Dict, Any, List, Optional
import logging
import httpx

from app.core.config import settings
from app.providers.social.base import BaseSocialProvider
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class TwitterProvider(BaseSocialProvider):
    """Official X (Twitter) API v2 Provider."""

    platform_name: str = "TWITTER"

    @classmethod
    def is_configured(cls) -> bool:
        # Check OAuth 2.0 Bearer or OAuth 1.0a User Access Token
        return bool(
            settings.TWITTER_BEARER_TOKEN
            or (settings.TWITTER_API_KEY and settings.TWITTER_ACCESS_TOKEN)
        )

    @classmethod
    def _get_auth_headers(cls) -> Dict[str, str]:
        token = settings.TWITTER_BEARER_TOKEN or settings.TWITTER_ACCESS_TOKEN
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def test_connection(cls) -> Dict[str, Any]:
        """Test X API v2 connection."""
        if not cls.is_configured():
            return {
                "configured": False,
                "status": "NOT_CONFIGURED",
                "message": "X (Twitter) API credentials (TWITTER_BEARER_TOKEN or TWITTER_ACCESS_TOKEN) are not configured.",
                "account_name": "X Account (Unconfigured)",
                "account_handle": "@unconfigured",
            }

        url = "https://api.twitter.com/2/users/me"
        params = {"user.fields": "profile_image_url,public_metrics"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=cls._get_auth_headers(), params=params)
                if res.status_code == 200:
                    data = res.json().get("data", {})
                    ProviderHealthService.record_success("twitter")
                    return {
                        "configured": True,
                        "status": "ACTIVE",
                        "account_name": data.get("name", "X Account"),
                        "account_handle": f"@{data.get('username', '')}",
                        "account_id": data.get("id"),
                        "followers_count": data.get("public_metrics", {}).get("followers_count", 0),
                        "profile_image_url": data.get("profile_image_url"),
                    }
                elif res.status_code in [401, 403]:
                    ProviderHealthService.record_failure("twitter", "Invalid bearer token", IntegrationStatus.INVALID_CREDENTIALS)
                    return {
                        "configured": True,
                        "status": "EXPIRED",
                        "error": "X API token is invalid or unauthorized for tweets endpoint.",
                    }
                else:
                    ProviderHealthService.record_failure("twitter", f"HTTP {res.status_code}")
                    return {
                        "configured": True,
                        "status": "ERROR",
                        "error": res.text,
                    }
        except Exception as e:
            logger.error(f"X API connection test error: {e}")
            ProviderHealthService.record_failure("twitter", str(e))
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
        """Publish a tweet via X API v2 (POST /2/tweets)."""
        if not cls.is_configured():
            logger.info("[TwitterProvider] Not configured. Post retained in NOT_CONFIGURED state.")
            return {
                "success": False,
                "provider_status": "NOT_CONFIGURED",
                "external_post_id": None,
                "external_post_url": None,
                "api_response": None,
                "error": "X (Twitter) credentials are not configured in .env. Retaining draft for manual publishing.",
            }

        url = "https://api.twitter.com/2/tweets"
        payload = {"text": caption}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, headers=cls._get_auth_headers(), json=payload)
                if res.status_code in [200, 201]:
                    data = res.json().get("data", {})
                    tweet_id = data.get("id")
                    ProviderHealthService.record_success("twitter")
                    return {
                        "success": True,
                        "provider_status": "LIVE_API",
                        "external_post_id": tweet_id,
                        "external_post_url": f"https://x.com/i/status/{tweet_id}",
                        "api_response": data,
                        "error": None,
                    }
                else:
                    err = res.text
                    logger.error(f"X API publish tweet failed: {err}")
                    return {
                        "success": False,
                        "provider_status": "FAILED",
                        "external_post_id": None,
                        "external_post_url": None,
                        "api_response": res.json() if res.headers.get("content-type", "").startswith("application/json") else {"text": err},
                        "error": f"X tweet failed: {err}",
                    }
        except Exception as e:
            logger.error(f"X API network error: {e}")
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
        """Fetch tweet public metrics from X API v2."""
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

        url = f"https://api.twitter.com/2/tweets/{external_post_id}"
        params = {"tweet.fields": "public_metrics"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(url, headers=cls._get_auth_headers(), params=params)
                if res.status_code == 200:
                    data = res.json().get("data", {})
                    metrics = data.get("public_metrics", {})
                    likes = metrics.get("like_count", 0)
                    retweets = metrics.get("retweet_count", 0)
                    replies = metrics.get("reply_count", 0)
                    impressions = metrics.get("impression_count", 0)
                    engagements = likes + retweets + replies
                    rate = (engagements / max(impressions, 1)) * 100
                    return {
                        "impressions": impressions,
                        "reach": impressions,
                        "engagement_count": engagements,
                        "likes": likes,
                        "comments": replies,
                        "shares": retweets,
                        "clicks": 0,
                        "engagement_rate": round(rate, 2),
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch X metrics: {e}")

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

