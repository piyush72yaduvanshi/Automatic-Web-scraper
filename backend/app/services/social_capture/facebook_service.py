"""Facebook lead extraction service."""

import logging
from datetime import datetime
from typing import List, Dict, Any
import httpx

from app.services.social_capture.base_extractor import BaseSocialExtractor
from app.services.social_capture.exceptions import RateLimitError, AuthenticationError, PlatformAPIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class FacebookLeadExtractor(BaseSocialExtractor):
    """Extract leads from Facebook page engagements."""
    
    def __init__(self, page_access_token: str = None, page_id: str = None):
        super().__init__("FACEBOOK")
        self.page_access_token = page_access_token or getattr(settings, "FACEBOOK_PAGE_ACCESS_TOKEN", None)
        self.page_id = page_id or getattr(settings, "FACEBOOK_PAGE_ID", None)
        self.base_url = "https://graph.facebook.com/v18.0"
    
    async def fetch_engagements(
        self,
        since_timestamp: datetime,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Facebook page comments and messages."""
        
        if not self.page_access_token or not self.page_id:
            logger.warning("Facebook credentials not configured")
            return []
        
        engagements = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch recent posts
                posts_response = await self._fetch_posts(client, since_timestamp)
                
                if posts_response:
                    # Fetch comments for each post
                    for post in posts_response.get("data", []):
                        comments = await self._fetch_comments(client, post["id"])
                        engagements.extend(comments)
                
                # Fetch page messages
                try:
                    messages = await self._fetch_page_messages(client, since_timestamp)
                    engagements.extend(messages)
                except Exception as e:
                    logger.debug(f"Could not fetch Facebook messages: {e}")
        
        except Exception as e:
            logger.error(f"Error fetching Facebook engagements: {e}", exc_info=True)
        
        return engagements
    
    async def _fetch_posts(self, client: httpx.AsyncClient, since_timestamp: datetime) -> Dict[str, Any]:
        """Fetch recent page posts."""
        url = f"{self.base_url}/{self.page_id}/posts"
        params = {
            "access_token": self.page_access_token,
            "fields": "id,message,created_time,permalink_url",
            "limit": 25,
        }
        
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 401 or response.status_code == 190:
                raise AuthenticationError("FACEBOOK", "Invalid page access token")
            elif response.status_code == 429:
                raise RateLimitError("FACEBOOK", retry_after=3600)
            elif response.status_code != 200:
                raise PlatformAPIError("FACEBOOK", response.status_code, response.text)
            
            return response.json()
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching Facebook posts: {e}")
            return {}
    
    async def _fetch_comments(self, client: httpx.AsyncClient, post_id: str) -> List[Dict[str, Any]]:
        """Fetch comments on a post."""
        url = f"{self.base_url}/{post_id}/comments"
        params = {
            "access_token": self.page_access_token,
            "fields": "id,message,from,created_time",
        }
        
        engagements = []
        
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for comment in data.get("data", []):
                    from_user = comment.get("from", {})
                    user_id = from_user.get("id")
                    user_name = from_user.get("name", "unknown")
                    
                    engagements.append({
                        "platform": "FACEBOOK",
                        "platform_user_id": user_id,
                        "social_username": user_name,
                        "social_profile_url": f"https://facebook.com/{user_id}",
                        "message_content": comment.get("message", ""),
                        "engagement_type": "COMMENT",
                        "engagement_url": None,
                        "post_context": None,
                        "engagement_timestamp": datetime.fromisoformat(comment.get("created_time", "").replace("Z", "+00:00")),
                        "raw_data": comment,
                    })
        
        except Exception as e:
            logger.error(f"Error fetching Facebook comments: {e}")
        
        return engagements
    
    async def _fetch_page_messages(self, client: httpx.AsyncClient, since_timestamp: datetime) -> List[Dict[str, Any]]:
        """Fetch Facebook page messages (Messenger)."""
        # Note: Requires pages_messaging permission
        logger.debug("Facebook Messenger fetching not fully implemented (requires pages_messaging permission)")
        return []
