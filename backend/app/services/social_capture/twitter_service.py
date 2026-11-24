"""Twitter/X lead extraction service."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx

from app.services.social_capture.base_extractor import BaseSocialExtractor
from app.services.social_capture.exceptions import RateLimitError, AuthenticationError, PlatformAPIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class TwitterLeadExtractor(BaseSocialExtractor):
    """Extract leads from Twitter/X mentions and replies."""
    
    def __init__(self, bearer_token: str = None):
        super().__init__("TWITTER")
        self.bearer_token = bearer_token or getattr(settings, "TWITTER_BEARER_TOKEN", None)
        self.base_url = "https://api.twitter.com/2"
    
    async def fetch_engagements(
        self,
        since_timestamp: datetime,
        user_id: str = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch Twitter mentions and replies."""
        
        if not self.bearer_token:
            logger.warning("Twitter credentials not configured")
            return []
        
        engagements = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch mentions (requires knowing our user ID)
                if user_id:
                    mentions = await self._fetch_mentions(client, user_id, since_timestamp)
                    engagements.extend(mentions)
                else:
                    logger.debug("Twitter user_id not provided, cannot fetch mentions")
        
        except Exception as e:
            logger.error(f"Error fetching Twitter engagements: {e}", exc_info=True)
        
        return engagements
    
    async def _fetch_mentions(
        self,
        client: httpx.AsyncClient,
        user_id: str,
        since_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch mentions of the user."""
        url = f"{self.base_url}/users/{user_id}/mentions"
        
        # Twitter API expects RFC3339 timestamp
        start_time = since_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        params = {
            "tweet.fields": "created_at,text,author_id",
            "user.fields": "username,name",
            "expansions": "author_id",
            "start_time": start_time,
            "max_results": 100,
        }
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}"
        }
        
        engagements = []
        
        try:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 401:
                raise AuthenticationError("TWITTER", "Invalid bearer token")
            elif response.status_code == 429:
                # Check rate limit reset time from headers
                reset_time = response.headers.get("x-rate-limit-reset", "900")
                raise RateLimitError("TWITTER", retry_after=int(reset_time))
            elif response.status_code != 200:
                raise PlatformAPIError("TWITTER", response.status_code, response.text)
            
            data = response.json()
            tweets = data.get("data", [])
            includes = data.get("includes", {})
            users = {user["id"]: user for user in includes.get("users", [])}
            
            for tweet in tweets:
                author_id = tweet.get("author_id")
                author = users.get(author_id, {})
                username = author.get("username", "unknown")
                
                engagements.append({
                    "platform": "TWITTER",
                    "platform_user_id": author_id,
                    "social_username": username,
                    "social_profile_url": f"https://twitter.com/{username}",
                    "message_content": tweet.get("text", ""),
                    "engagement_type": "MENTION",
                    "engagement_url": f"https://twitter.com/{username}/status/{tweet['id']}",
                    "post_context": None,
                    "engagement_timestamp": datetime.fromisoformat(tweet.get("created_at", "").replace("Z", "+00:00")),
                    "raw_data": tweet,
                })
        
        except RateLimitError:
            raise
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error fetching Twitter mentions: {e}")
        
        return engagements
