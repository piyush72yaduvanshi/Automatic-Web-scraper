"""Webhook models for outbound event notifications and subscriptions."""

import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class WebhookSubscription(Base):
    """Stores third-party webhook subscriptions listening for platform events."""

    __tablename__ = "webhook_subscriptions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    target_url = Column(String(500), nullable=False)
    secret_key = Column(String(100), nullable=False, default=lambda: secrets.token_hex(24))
    
    # List of subscribed events, e.g. ["*"] or ["lead.discovered", "lead.qualified", "lead.contacted"]
    events = Column(JSON, nullable=False, default=list)
    
    is_active = Column(Boolean, default=True, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    last_delivery_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    deliveries = relationship("WebhookDelivery", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WebhookSubscription(id={self.id}, name='{self.name}', url='{self.target_url}')>"


class WebhookDelivery(Base):
    """Audit log of dispatched webhook HTTP requests."""

    __tablename__ = "webhook_deliveries"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    subscription_id = Column(GUID, ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    attempt = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    subscription = relationship("WebhookSubscription", back_populates="deliveries")

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, event='{self.event}', status={self.status_code})>"
