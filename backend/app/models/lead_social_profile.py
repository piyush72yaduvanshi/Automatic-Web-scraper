"""Lead Social Profile database model."""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SocialPlatform(str, Enum):
    """Social media platform enumeration."""
    INSTAGRAM = "INSTAGRAM"
    LINKEDIN = "LINKEDIN"
    FACEBOOK = "FACEBOOK"
    X = "X"


class LeadSocialProfile(Base):
    """Social media profiles for business leads."""
    
    __tablename__ = "lead_social_profiles"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    lead_id = Column(UUID(as_uuid=True), ForeignKey("business_leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Social Information
    platform = Column(SQLEnum(SocialPlatform), nullable=False)
    profile_url = Column(String(500), nullable=False)
    
    # Verification
    verification_status = Column(String(50), default="unverified")
    
    # Source
    source_url = Column(Text)
    
    # Timestamp
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    lead = relationship("BusinessLead", back_populates="social_profiles")
    
    # Indexes
    __table_args__ = (
        Index("idx_lead_platform", "lead_id", "platform"),
        Index("idx_profile_url", "profile_url"),
    )
    
    def __repr__(self):
        return f"<LeadSocialProfile(id={self.id}, platform={self.platform}, url='{self.profile_url}')>"
