"""Base Social Provider Interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseSocialProvider(ABC):
    """Abstract interface for official social media platform providers."""

    platform_name: str = "generic"

    @classmethod
    @abstractmethod
    def is_configured(cls) -> bool:
        """Check if required API credentials/tokens are configured."""
        pass

    @classmethod
    @abstractmethod
    async def test_connection(cls) -> Dict[str, Any]:
        """Verify API credentials and retrieve basic profile info."""
        pass

    @classmethod
    @abstractmethod
    async def publish_post(
        cls,
        caption: str,
        media_urls: Optional[List[str]] = None,
        creative_brief: Optional[Dict[str, Any]] = None,
        account_id_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publish post to official platform API.
        
        Must return a dictionary:
        {
            "success": bool,
            "provider_status": "LIVE_API" | "NOT_CONFIGURED" | "FAILED",
            "external_post_id": Optional[str],
            "external_post_url": Optional[str],
            "api_response": Optional[Dict[str, Any]],
            "error": Optional[str]
        }
        """
        pass

    @classmethod
    @abstractmethod
    async def get_post_metrics(cls, external_post_id: str) -> Dict[str, Any]:
        """
        Fetch live engagement metrics from platform API.
        Returns impressions, reach, likes, comments, shares, clicks, etc.
        """
        pass
