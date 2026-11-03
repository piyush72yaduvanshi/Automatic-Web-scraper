"""Lead Contact database model."""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContactType(str, Enum):
    """Contact type enumeration."""
    PHONE = "PHONE"
    EMAIL = "EMAIL"


class LeadContact(Base):
    """Contact information for business leads."""
    
    __tablename__ = "lead_contacts"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    lead_id = Column(UUID(as_uuid=True), ForeignKey("business_leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Contact Information
    contact_type = Column(SQLEnum(ContactType), nullable=False)
    original_value = Column(String(500), nullable=False)
    normalized_value = Column(String(500), index=True)
    
    # Verification
    verification_status = Column(String(50), default="unverified")
    
    # Source
    source_url = Column(Text)
    
    # Timestamp
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    lead = relationship("BusinessLead", back_populates="contacts")
    
    # Indexes
    __table_args__ = (
        Index("idx_lead_contact_type", "lead_id", "contact_type"),
        Index("idx_normalized_value", "normalized_value"),
    )
    
    def __repr__(self):
        return f"<LeadContact(id={self.id}, type={self.contact_type}, value='{self.normalized_value}')>"
