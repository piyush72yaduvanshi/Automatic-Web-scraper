"""Pydantic schemas for social media leads and inbound messages."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# Enums
class PlatformEnum(str):
    """Social media platforms."""
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    TWITTER = "TWITTER"
    LINKEDIN = "LINKEDIN"


class ChannelEnum(str):
    """Inbound message channels."""
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    SMS = "SMS"


class EngagementTypeEnum(str):
    """Types of social media engagement."""
    COMMENT = "COMMENT"
    DM = "DM"
    MENTION = "MENTION"
    REPLY = "REPLY"
    CONNECTION_REQUEST = "CONNECTION_REQUEST"
    PROFILE_VIEW = "PROFILE_VIEW"
    STORY_REPLY = "STORY_REPLY"
    POST_REACTION = "POST_REACTION"


class SentimentEnum(str):
    """Sentiment classification."""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    INTERESTED = "INTERESTED"


class MessageClassificationEnum(str):
    """Inbound message classification."""
    INTERESTED = "INTERESTED"
    OBJECTION = "OBJECTION"
    NOT_NOW = "NOT_NOW"
    UNSUBSCRIBE = "UNSUBSCRIBE"
    QUESTION = "QUESTION"
    OUT_OF_OFFICE = "OUT_OF_OFFICE"


# Social Media Lead Schemas
class SocialMediaLeadBase(BaseModel):
    """Base schema for social media lead."""
    platform: str = Field(..., description="Social media platform")
    social_profile_url: str = Field(..., description="URL to social profile")
    social_username: str = Field(..., description="Social media username")
    message_content: Optional[str] = Field(None, description="Message or comment content")
    engagement_type: str = Field(..., description="Type of engagement")
    engagement_url: Optional[str] = Field(None, description="URL to the engagement")
    post_context: Optional[str] = Field(None, description="Context of the post")
    sentiment: Optional[str] = Field(None, description="Sentiment classification")
    interest_score: float = Field(0.5, ge=0.0, le=1.0, description="Interest score")
    platform_user_id: Optional[str] = Field(None, description="Platform user ID")
    engagement_timestamp: datetime = Field(..., description="When engagement occurred")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw platform data")


class SocialMediaLeadCreate(SocialMediaLeadBase):
    """Schema for creating a social media lead."""
    pass


class SocialMediaLeadUpdate(BaseModel):
    """Schema for updating a social media lead."""
    processed: Optional[bool] = None
    processing_notes: Optional[str] = None
    lead_id: Optional[UUID] = None
    sentiment: Optional[str] = None
    interest_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class SocialMediaLeadInDB(SocialMediaLeadBase):
    """Schema for social media lead in database."""
    id: UUID
    lead_id: Optional[UUID]
    processed: bool
    processing_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SocialMediaLeadResponse(SocialMediaLeadInDB):
    """Schema for social media lead API response."""
    pass


# Inbound Message Schemas
class InboundMessageBase(BaseModel):
    """Base schema for inbound message."""
    channel: str = Field(..., description="Message channel")
    sender_contact: str = Field(..., description="Sender email or phone")
    message_body: str = Field(..., description="Message content")
    subject: Optional[str] = Field(None, description="Email subject")
    interest_score: float = Field(0.5, ge=0.0, le=1.0, description="Interest score")
    sentiment: Optional[str] = Field(None, description="Sentiment")
    classification: Optional[str] = Field(None, description="Message classification")
    suggested_reply: Optional[str] = Field(None, description="AI-suggested reply")
    thread_id: Optional[str] = Field(None, description="Thread ID")
    in_reply_to_message_id: Optional[str] = Field(None, description="Reply-to message ID")
    campaign_id: Optional[UUID] = Field(None, description="Related campaign ID")
    requires_human_attention: bool = Field(False, description="Needs human review")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    platform_message_id: Optional[str] = Field(None, description="Platform message ID")
    received_at: datetime = Field(..., description="When message was received")


class InboundMessageCreate(InboundMessageBase):
    """Schema for creating an inbound message."""
    pass


class InboundMessageUpdate(BaseModel):
    """Schema for updating an inbound message."""
    processed: Optional[bool] = None
    processed_at: Optional[datetime] = None
    lead_id: Optional[UUID] = None
    classification: Optional[str] = None
    sentiment: Optional[str] = None
    interest_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    suggested_reply: Optional[str] = None
    requires_human_attention: Optional[bool] = None


class InboundMessageInDB(InboundMessageBase):
    """Schema for inbound message in database."""
    id: UUID
    lead_id: Optional[UUID]
    processed: bool
    processed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class InboundMessageResponse(InboundMessageInDB):
    """Schema for inbound message API response."""
    pass


# Statistics Schemas
class SocialLeadStats(BaseModel):
    """Statistics for social lead capture."""
    total_engagements: int = Field(..., description="Total engagements captured")
    by_platform: Dict[str, int] = Field(..., description="Engagements by platform")
    by_engagement_type: Dict[str, int] = Field(..., description="Engagements by type")
    processed_count: int = Field(..., description="Processed engagements")
    unprocessed_count: int = Field(..., description="Unprocessed engagements")
    converted_to_leads: int = Field(..., description="Converted to leads")
    average_interest_score: float = Field(..., description="Average interest score")
    last_captured_at: Optional[datetime] = Field(None, description="Last capture time")


class InboundMessageStats(BaseModel):
    """Statistics for inbound messages."""
    total_messages: int = Field(..., description="Total messages")
    by_channel: Dict[str, int] = Field(..., description="Messages by channel")
    by_classification: Dict[str, int] = Field(..., description="Messages by classification")
    processed_count: int = Field(..., description="Processed messages")
    requires_attention_count: int = Field(..., description="Messages needing attention")
    average_interest_score: float = Field(..., description="Average interest score")
    last_received_at: Optional[datetime] = Field(None, description="Last message time")


# Manual Lead Creation Schema
class ManualSocialLeadCreate(BaseModel):
    """Schema for manually creating a social lead."""
    platform: str
    social_username: str
    social_profile_url: str
    message_content: Optional[str] = None
    engagement_type: str
    notes: Optional[str] = None
