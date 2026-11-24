"""Social Media Lead database models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class SocialMediaLead(Base):
    """Captures lead-qualifying engagement from social media platforms."""
    
    __tablename__ = "social_media_leads"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('business_leads.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Platform Information
    platform = Column(String(50), nullable=False, index=True)  # INSTAGRAM, FACEBOOK, TWITTER, LINKEDIN
    social_profile_url = Column(String(500), nullable=False)
    social_username = Column(String(200), nullable=False, index=True)
    
    # Engagement Data
    message_content = Column(Text, nullable=True)
    engagement_type = Column(String(100), nullable=False)  # COMMENT, DM, MENTION, REPLY, etc.
    engagement_url = Column(String(500), nullable=True)
    
    # Lead Context
    post_context = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)  # POSITIVE, NEUTRAL, NEGATIVE, INTERESTED
    interest_score = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Processing
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processing_notes = Column(Text, nullable=True)
    
    # Metadata
    platform_user_id = Column(String(255), nullable=True)
    engagement_timestamp = Column(DateTime, nullable=False, index=True)
    raw_data = Column(JSONB, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    lead = relationship("BusinessLead", foreign_keys=[lead_id])
    
    def __repr__(self):
        return f"<SocialMediaLead(id={self.id}, platform='{self.platform}', username='{self.social_username}')>"


class InboundMessage(Base):
    """Captures inbound messages from email replies and WhatsApp."""
    
    __tablename__ = "inbound_messages"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('business_leads.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Channel Information
    channel = Column(String(50), nullable=False, index=True)  # EMAIL, WHATSAPP, SMS
    sender_contact = Column(String(255), nullable=False, index=True)
    
    # Message Content
    message_body = Column(Text, nullable=False)
    subject = Column(String(500), nullable=True)
    
    # Lead Intelligence
    interest_score = Column(Float, default=0.5)
    sentiment = Column(String(50), nullable=True)
    classification = Column(String(100), nullable=True, index=True)  # INTERESTED, OBJECTION, etc.
    suggested_reply = Column(Text, nullable=True)
    
    # Context
    thread_id = Column(String(255), nullable=True, index=True)
    in_reply_to_message_id = Column(String(255), nullable=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Processing
    processed = Column(Boolean, default=False, nullable=False, index=True)
    requires_human_attention = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    message_metadata = Column(JSONB, nullable=True)
    platform_message_id = Column(String(255), nullable=True)
    
    # Audit
    received_at = Column(DateTime, nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    lead = relationship("BusinessLead", foreign_keys=[lead_id])
    
    def __repr__(self):
        return f"<InboundMessage(id={self.id}, channel='{self.channel}', sender='{self.sender_contact}')>"
