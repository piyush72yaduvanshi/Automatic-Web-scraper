"""Instagram lead extraction service."""

import logging
from datetime import datetime
from typing import List, Dict, Any
import httpx

from app.services.social_capture.base_extractor import BaseSocialExtractor
from app.services.social_capture.exceptions import RateLimitError, AuthenticationError, PlatformAPIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class InstagramLeadExtractor(BaseSocialExtractor):
    """Extract leads from Instagram engagements."""
    
    def __init__(self, access_token: str = None, business_account_id: str = None):
        super().__init__("INSTAGRAM")
        self.access_token = access_token or getattr(settings, "INSTAGRAM_ACCESS_TOKEN", None)
        self.business_account_id = business_account_id or getattr(settings, "INSTAGRAM_BUSINESS_ACCOUNT_ID", None)
        self.base_url = "https://graph.instagram.com/v18.0"
    
    async def fetch_engagements(
        self,
        since_timestamp: datetime,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Instagram comments, DMs, and story replies."""
        
        if not self.access_token or not self.business_account_id:
            logger.warning("Instagram credentials not configured")
            return []
        
        engagements = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch recent media
                media_response = await self._fetch_media(client, since_timestamp)
                
                if media_response:
                    # Fetch comments for each media
                    for media in media_response.get("data", []):
                        comments = await self._fetch_comments(client, media["id"])
                        engagements.extend(comments)
                
                # Fetch direct messages (requires additional permissions)
                try:
                    dms = await self._fetch_direct_messages(client, since_timestamp)
                    engagements.extend(dms)
                except Exception as e:
                    logger.debug(f"Could not fetch Instagram DMs: {e}")
        
        except Exception as e:
            logger.error(f"Error fetching Instagram engagements: {e}", exc_info=True)
        
        return engagements
    
    async def _fetch_media(self, client: httpx.AsyncClient, since_timestamp: datetime) -> Dict[str, Any]:
        """Fetch recent media posts."""
        url = f"{self.base_url}/{self.business_account_id}/media"
        params = {
            "access_token": self.access_token,
            "fields": "id,caption,media_type,timestamp,permalink",
            "limit": 25,
        }
        
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 401:
                raise AuthenticationError("INSTAGRAM", "Invalid access token")
            elif response.status_code == 429:
                raise RateLimitError("INSTAGRAM", retry_after=3600)
            elif response.status_code != 200:
                raise PlatformAPIError("INSTAGRAM", response.status_code, response.text)
            
            return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching Instagram media: {e}")
            return {}
    
    async def _fetch_comments(self, client: httpx.AsyncClient, media_id: str) -> List[Dict[str, Any]]:
        """Fetch comments on a media post."""
        url = f"{self.base_url}/{media_id}/comments"
        params = {
            "access_token": self.access_token,
            "fields": "id,text,username,timestamp,from",
        }
        
        engagements = []
        
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for comment in data.get("data", []):
                    engagements.append({
                        "platform": "INSTAGRAM",
                        "platform_user_id": comment.get("from", {}).get("id"),
                        "social_username": comment.get("username", "unknown"),
                        "social_profile_url": f"https://instagram.com/{comment.get('username', '')}",
                        "message_content": comment.get("text", ""),
                        "engagement_type": "COMMENT",
                        "engagement_url": None,
                        "post_context": None,
                        "engagement_timestamp": datetime.fromisoformat(comment.get("timestamp", "").replace("Z", "+00:00")),
                        "raw_data": comment,
                    })
        
        except Exception as e:
            logger.error(f"Error fetching Instagram comments: {e}")
        
        return engagements
    
    async def _fetch_direct_messages(self, client: httpx.AsyncClient, since_timestamp: datetime) -> List[Dict[str, Any]]:
        """Fetch Instagram direct messages (requires instagram_manage_messages permission)."""
        # Note: This requires additional permissions and Instagram approval
        # Placeholder implementation
        logger.debug("Instagram DM fetching not fully implemented (requires instagram_manage_messages permission)")
        return []
