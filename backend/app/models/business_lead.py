"""Business Lead database model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Index, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class BusinessLead(Base):
    """Business lead information from discovery providers."""
    
    __tablename__ = "business_leads"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Business Information
    business_name = Column(String(500), nullable=False, index=True)
    category = Column(String(200), index=True)
    description = Column(Text)
    
    # Location
    address = Column(Text)
    city = Column(String(200), index=True)
    state = Column(String(200), index=True)
    country = Column(String(100), index=True)
    
    # Contact
    website = Column(String(500), index=True)
    
    # Source Information
    source_provider = Column(String(100), nullable=False)
    provider_external_id = Column(String(500), unique=True)
    
    # Status & Qualification
    status = Column(String(50), default="discovered", index=True)
    qualification_score = Column(Float, nullable=True, default=50.0)
    qualification_status = Column(String(50), default="New", index=True)
    qualification_reasoning = Column(Text, nullable=True)
    qualification_breakdown = Column(Text, nullable=True)  # JSON
    company_research = Column(Text, nullable=True)  # JSON
    data_confidence_score = Column(Float, default=50.0)
    company_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Automation tracking
    outreach_enrolled = Column(Boolean, default=False, server_default='false', index=True)
    outreach_enrollment_date = Column(DateTime, nullable=True)
    crm_converted = Column(Boolean, default=False, server_default='false', index=True)
    crm_conversion_date = Column(DateTime, nullable=True)
    email_enrichment_status = Column(String(50), default='pending', server_default='pending')
    last_automation_run = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    contacts = relationship(
        "LeadContact",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    social_profiles = relationship(
        "LeadSocialProfile",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    source_evidence = relationship(
        "LeadSourceEvidence",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_business_name_city", "business_name", "city"),
        Index("idx_category_city", "category", "city"),
        Index("idx_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<BusinessLead(id={self.id}, name='{self.business_name}', city='{self.city}')>"
