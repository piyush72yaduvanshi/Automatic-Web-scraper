"""Base class for social media lead extraction."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.social_media_lead import SocialMediaLead
from app.models.business_lead import BusinessLead
from app.services.social_capture.exceptions import SocialCaptureError

logger = logging.getLogger(__name__)


class BaseSocialExtractor(ABC):
    """Base class for social media lead extractors."""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.logger = logging.getLogger(f"{__name__}.{platform}")
    
    @abstractmethod
    async def fetch_engagements(
        self,
        since_timestamp: datetime,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch engagements from the platform.
        
        Args:
            since_timestamp: Fetch engagements since this time
            **kwargs: Platform-specific parameters
            
        Returns:
            List of engagement dictionaries
        """
        pass
    
    def extract_contact_info(self, engagement: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """
        Extract contact information from engagement.
        
        Args:
            engagement: Engagement data
            
        Returns:
            Dictionary with email, phone, name if found
        """
        contact_info = {
            "email": None,
            "phone": None,
            "name": None,
        }
        
        # Extract from message content
        message = engagement.get("message_content", "")
        
        # Simple email extraction (improve with regex)
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails:
            contact_info["email"] = emails[0]
        
        # Simple phone extraction (improve with phonenumbers library)
        phone_pattern = r'\+?[\d\s\-\(\)]{10,}'
        phones = re.findall(phone_pattern, message)
        if phones:
            contact_info["phone"] = phones[0].strip()
        
        return contact_info
    
    def detect_business_intent(self, message: str) -> tuple[float, str]:
        """
        Detect business intent and interest level from message.
        
        Args:
            message: Message content
            
        Returns:
            Tuple of (interest_score, sentiment)
        """
        if not message:
            return 0.5, "NEUTRAL"
        
        message_lower = message.lower()
        
        # High interest keywords
        high_interest_keywords = [
            "interested", "pricing", "demo", "meeting", "call", "quote",
            "proposal", "price", "cost", "buy", "purchase", "order",
            "contact", "reach out", "discuss", "learn more", "tell me more"
        ]
        
        # Medium interest keywords
        medium_interest_keywords = [
            "info", "information", "details", "help", "how", "what",
            "when", "where", "can you", "do you"
        ]
        
        # Negative keywords
        negative_keywords = [
            "not interested", "no thanks", "stop", "unsubscribe", "spam",
            "remove", "never", "don't contact"
        ]
        
        # Calculate score
        high_count = sum(1 for kw in high_interest_keywords if kw in message_lower)
        medium_count = sum(1 for kw in medium_interest_keywords if kw in message_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in message_lower)
        
        if negative_count > 0:
            return 0.2, "NEGATIVE"
        elif high_count > 0:
            return 0.8 + (0.05 * high_count), "INTERESTED"
        elif medium_count > 0:
            return 0.6, "POSITIVE"
        else:
            return 0.5, "NEUTRAL"
    
    async def create_lead_from_engagement(
        self,
        engagement: Dict[str, Any],
        db: Session
    ) -> Optional[SocialMediaLead]:
        """
        Create a social media lead from engagement data.
        
        Args:
            engagement: Engagement data
            db: Database session
            
        Returns:
            Created SocialMediaLead or None if already exists
        """
        try:
            # Detect interest and sentiment
            message = engagement.get("message_content", "")
            interest_score, sentiment = self.detect_business_intent(message)
            
            # Create social media lead record
            social_lead = SocialMediaLead(
                platform=self.platform,
                social_profile_url=engagement.get("social_profile_url", ""),
                social_username=engagement.get("social_username", ""),
                message_content=message,
                engagement_type=engagement.get("engagement_type", ""),
                engagement_url=engagement.get("engagement_url"),
                post_context=engagement.get("post_context"),
                sentiment=sentiment,
                interest_score=interest_score,
                platform_user_id=engagement.get("platform_user_id"),
                engagement_timestamp=engagement.get("engagement_timestamp", datetime.utcnow()),
                raw_data=engagement.get("raw_data"),
                processed=False,
            )
            
            db.add(social_lead)
            db.commit()
            db.refresh(social_lead)
            
            self.logger.info(
                f"Created social lead: {social_lead.id} from {self.platform} "
                f"user {social_lead.social_username} (score: {interest_score})"
            )
            
            return social_lead
            
        except IntegrityError as e:
            db.rollback()
            self.logger.debug(f"Duplicate engagement detected: {e}")
            return None
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating social lead: {e}", exc_info=True)
            raise SocialCaptureError(f"Failed to create social lead: {e}")
    
    async def convert_to_business_lead(
        self,
        social_lead: SocialMediaLead,
        db: Session
    ) -> Optional[BusinessLead]:
        """
        Convert social media lead to business lead.
        
        Args:
            social_lead: Social media lead
            db: Database session
            
        Returns:
            Created BusinessLead or existing one
        """
        # Check if lead already exists
        if social_lead.lead_id:
            return db.query(BusinessLead).filter(BusinessLead.id == social_lead.lead_id).first()
        
        # Extract contact info
        contact_info = self.extract_contact_info({
            "message_content": social_lead.message_content
        })
        
        # Create business lead
        business_lead = BusinessLead(
            business_name=social_lead.social_username,
            description=f"Lead captured from {self.platform}: {social_lead.message_content[:200]}",
            website=social_lead.social_profile_url,
            source_provider=f"SOCIAL_{self.platform}",
            provider_external_id=f"{self.platform}_{social_lead.platform_user_id}",
            status="discovered",
            lead_source="SOCIAL_MEDIA",
            qualification_score=social_lead.interest_score * 100,
            qualification_status="New",
            social_engagement_count=1,
            last_social_engagement_at=social_lead.engagement_timestamp,
        )
        
        db.add(business_lead)
        db.commit()
        db.refresh(business_lead)
        
        # Link social lead to business lead
        social_lead.lead_id = business_lead.id
        social_lead.processed = True
        db.commit()
        
        self.logger.info(f"Converted social lead {social_lead.id} to business lead {business_lead.id}")
        
        return business_lead
    
    async def store_engagements(
        self,
        engagements: List[Dict[str, Any]],
        db: Session
    ) -> Dict[str, int]:
        """
        Store multiple engagements in database.
        
        Args:
            engagements: List of engagement dictionaries
            db: Database session
            
        Returns:
            Dictionary with counts of created and duplicate leads
        """
        created_count = 0
        duplicate_count = 0
        error_count = 0
        
        for engagement in engagements:
            try:
                social_lead = await self.create_lead_from_engagement(engagement, db)
                if social_lead:
                    created_count += 1
                else:
                    duplicate_count += 1
            except Exception as e:
                error_count += 1
                self.logger.error(f"Error storing engagement: {e}")
        
        self.logger.info(
            f"Stored {created_count} new engagements from {self.platform} "
            f"({duplicate_count} duplicates, {error_count} errors)"
        )
        
        return {
            "created": created_count,
            "duplicates": duplicate_count,
            "errors": error_count,
        }
