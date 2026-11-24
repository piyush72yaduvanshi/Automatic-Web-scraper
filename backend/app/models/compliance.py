"""Global Consent, Marketing Eligibility, and GDPR/CAN-SPAM Compliance Models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Index

from app.core.database import Base
from app.models.guid import GUID


class ConsentRecord(Base):
    """Centralized consent and lawful basis audit record for contacts and recipients."""

    __tablename__ = "consent_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    recipient = Column(String(255), nullable=False, unique=True, index=True)  # Email or normalized phone
    contact_id = Column(GUID(), nullable=True, index=True)
    
    # Source: GOOGLE_MAPS, WEBSITE_INQUIRY, CSV_IMPORT, DIRECT_MEETING, MANUAL
    source = Column(String(100), default="MANUAL")
    source_url = Column(String(500), nullable=True)
    
    # Lawful Basis: CONSENT, LEGITIMATE_INTEREST, CONTRACT, PUBLIC_INFORMATION
    lawful_basis = Column(String(100), default="LEGITIMATE_INTEREST")
    
    channel_email_consent = Column(Boolean, default=True)
    channel_whatsapp_consent = Column(Boolean, default=False)  # Explicit opt-in required for WhatsApp
    marketing_eligible = Column(Boolean, default=True, index=True)
    
    compliance_notes = Column(Text, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DataDeletionRequest(Base):
    """GDPR / CCPA 'Right to be Forgotten' data erasure and suppression request."""

    __tablename__ = "data_deletion_requests"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    recipient = Column(String(255), nullable=False, index=True)
    reason = Column(String(255), default="USER_REQUEST")
    
    # Statuses: REQUESTED, PROCESSING, COMPLETED
    status = Column(String(50), default="REQUESTED", index=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    audit_notes = Column(Text, nullable=True)

