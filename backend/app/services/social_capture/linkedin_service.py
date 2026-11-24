"""LinkedIn lead extraction service."""

import logging
from datetime import datetime
from typing import List, Dict, Any
import httpx

from app.services.social_capture.base_extractor import BaseSocialExtractor
from app.services.social_capture.exceptions import RateLimitError, AuthenticationError, PlatformAPIError
from app.core.config import settings

logger = logging.getLogger(__name__)


class LinkedInLeadExtractor(BaseSocialExtractor):
    """Extract leads from LinkedIn organization posts and connections."""
    
    def __init__(self, access_token: str = None, org_id: str = None):
        super().__init__("LINKEDIN")
        self.access_token = access_token or getattr(settings, "LINKEDIN_ACCESS_TOKEN", None)
        self.org_id = org_id or getattr(settings, "LINKEDIN_ORG_ID", None)
        self.base_url = "https://api.linkedin.com/v2"
    
    async def fetch_engagements(
        self,
        since_timestamp: datetime,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch LinkedIn post comments and connection requests."""
        
        if not self.access_token:
            logger.warning("LinkedIn credentials not configured")
            return []
        
        engagements = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch organization shares (posts)
                shares = await self._fetch_organization_shares(client, since_timestamp)
                
                # Fetch comments on shares
                for share in shares:
                    comments = await self._fetch_share_comments(client, share["id"])
                    engagements.extend(comments)
        
        except Exception as e:
            logger.error(f"Error fetching LinkedIn engagements: {e}", exc_info=True)
        
        return engagements
    
    async def _fetch_organization_shares(
        self,
        client: httpx.AsyncClient,
        since_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch organization posts (shares)."""
        
        if not self.org_id:
            logger.warning("LinkedIn organization ID not configured")
            return []
        
        url = f"{self.base_url}/shares"
        params = {
            "q": "owners",
            "owners": f"urn:li:organization:{self.org_id}",
            "count": 50,
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        
        shares = []
        
        try:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 401:
                raise AuthenticationError("LINKEDIN", "Invalid access token")
            elif response.status_code == 429:
                raise RateLimitError("LINKEDIN", retry_after=86400)  # Daily limit
            elif response.status_code != 200:
                raise PlatformAPIError("LINKEDIN", response.status_code, response.text)
            
            data = response.json()
            shares = data.get("elements", [])
        
        except Exception as e:
            logger.error(f"Error fetching LinkedIn shares: {e}")
        
        return shares
    
    async def _fetch_share_comments(
        self,
        client: httpx.AsyncClient,
        share_urn: str
    ) -> List[Dict[str, Any]]:
        """Fetch comments on a share."""
        url = f"{self.base_url}/socialActions/{share_urn}/comments"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        
        engagements = []
        
        try:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                for comment in data.get("elements", []):
                    actor = comment.get("actor", "")
                    message = comment.get("message", {}).get("text", "")
                    created = comment.get("created", {}).get("time", 0)
                    
                    # Extract user ID from actor URN
                    user_id = actor.split(":")[-1] if actor else "unknown"
                    
                    engagements.append({
                        "platform": "LINKEDIN",
                        "platform_user_id": user_id,
                        "social_username": user_id,
                        "social_profile_url": f"https://linkedin.com/in/{user_id}",
                        "message_content": message,
                        "engagement_type": "COMMENT",
                        "engagement_url": None,
                        "post_context": None,
                        "engagement_timestamp": datetime.fromtimestamp(created / 1000) if created else datetime.utcnow(),
                        "raw_data": comment,
                    })
        
        except Exception as e:
            logger.error(f"Error fetching LinkedIn comments: {e}")
        
        return engagements
