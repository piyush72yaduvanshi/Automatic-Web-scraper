"""Email Deliverability, Mailbox Health, and Domain Authentication Models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class EmailAccount(Base):
    """Connected mailbox account for sending and synchronization."""

    __tablename__ = "email_accounts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email_address = Column(String(255), nullable=False, unique=True, index=True)
    provider = Column(String(50), default="GMAIL")  # GMAIL, SMTP, SENDGRID, MOCK
    oauth_status = Column(String(50), default="NOT_CONFIGURED", index=True)  # CONNECTED, EXPIRED, NOT_CONFIGURED
    token_expires_at = Column(DateTime, nullable=True)
    sending_permissions = Column(Boolean, default=True)
    daily_quota = Column(Integer, default=50)
    sent_today = Column(Integer, default=0)
    
    last_sync_at = Column(DateTime, nullable=True)
    last_send_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Mailbox Health: HEALTHY, WARMING, DEGRADED, RESTRICTED
    health_status = Column(String(50), default="HEALTHY", index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EmailDomain(Base):
    """Domain DNS authentication records (SPF, DKIM, DMARC, MX)."""

    __tablename__ = "email_domains"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    domain_name = Column(String(255), nullable=False, unique=True, index=True)
    
    # DNS Statuses: VERIFIED, FAILED, UNAVAILABLE, UNVERIFIED
    spf_status = Column(String(50), default="UNVERIFIED")
    dkim_status = Column(String(50), default="UNVERIFIED")
    dmarc_status = Column(String(50), default="UNVERIFIED")
    mx_status = Column(String(50), default="UNVERIFIED")
    
    dns_records_json = Column(Text, nullable=True)  # JSON representation of detected DNS TXT/MX records
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EmailEvent(Base):
    """Granular email lifecycle events: queued, sent, delivered, bounced, complained, replied."""

    __tablename__ = "email_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email_account_id = Column(GUID(), ForeignKey("email_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = Column(GUID(), nullable=True, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    
    # Event Types: QUEUED, SENT, DELIVERED, BOUNCED, FAILED, REPLIED, UNSUBSCRIBED, COMPLAINED
    event_type = Column(String(50), nullable=False, index=True)
    event_payload = Column(Text, nullable=True)  # JSON payload
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
