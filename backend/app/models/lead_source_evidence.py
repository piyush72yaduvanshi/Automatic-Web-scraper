"""Lead Source Evidence database model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LeadSourceEvidence(Base):
    """Source evidence for lead data extraction."""
    
    __tablename__ = "lead_source_evidence"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    lead_id = Column(UUID(as_uuid=True), ForeignKey("business_leads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Evidence Information
    field_name = Column(String(100), nullable=False)
    extracted_value = Column(Text, nullable=False)
    source_url = Column(Text, nullable=False)
    provider = Column(String(100))
    
    # Timestamp
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    lead = relationship("BusinessLead", back_populates="source_evidence")
    
    # Indexes
    __table_args__ = (
        Index("idx_lead_field", "lead_id", "field_name"),
    )
    
    def __repr__(self):
        return f"<LeadSourceEvidence(id={self.id}, field='{self.field_name}', source='{self.source_url}')>"
