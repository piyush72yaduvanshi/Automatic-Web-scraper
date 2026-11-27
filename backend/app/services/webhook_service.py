"""Enterprise Webhook Dispatcher and External Ingestion Service.

Provides outbound event notifications with HMAC-SHA256 signatures,
retry handling, delivery audit logs, and external lead ingestion.
"""

import hmac
import hashlib
import json
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.webhook import WebhookSubscription, WebhookDelivery
from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType
from app.models.lead_social_profile import LeadSocialProfile, SocialPlatform

logger = logging.getLogger(__name__)


class WebhookService:
    """Manages outbound event dispatches and external CRM webhook ingestion."""

    @classmethod
    def generate_signature(cls, payload_bytes: bytes, secret_key: str) -> str:
        """Compute HMAC-SHA256 signature for webhook payload."""
        computed = hmac.new(
            secret_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={computed}"

    @classmethod
    def verify_signature(cls, payload_bytes: bytes, signature_header: str, secret_key: str) -> bool:
        """
        Verify incoming webhook signature using constant-time comparison.
        Prevents timing attacks.
        """
        if not signature_header or not secret_key:
            return False

        expected = cls.generate_signature(payload_bytes, secret_key)
        # Handle cases where header has or lacks "sha256=" prefix
        if signature_header.startswith("sha256="):
            return hmac.compare_digest(expected, signature_header)
        else:
            return hmac.compare_digest(expected.replace("sha256=", ""), signature_header)

    @classmethod
    def create_subscription(
        cls,
        db: Session,
        name: str,
        target_url: str,
        events: Optional[List[str]] = None,
        secret_key: Optional[str] = None,
    ) -> WebhookSubscription:
        """Register a new webhook subscriber endpoint."""
        sub = WebhookSubscription(
            name=name,
            target_url=target_url,
            events=events or ["*"],
        )
        if secret_key:
            sub.secret_key = secret_key

        db.add(sub)
        db.commit()
        db.refresh(sub)
        logger.info(f"Created webhook subscription {sub.id} -> {sub.target_url} for events: {sub.events}")
        return sub

    @classmethod
    def list_subscriptions(cls, db: Session, active_only: bool = False) -> List[WebhookSubscription]:
        """List registered webhook subscriptions."""
        query = db.query(WebhookSubscription)
        if active_only:
            query = query.filter(WebhookSubscription.is_active == True)
        return query.order_by(WebhookSubscription.created_at.desc()).all()

    @classmethod
    def delete_subscription(cls, db: Session, subscription_id: str) -> bool:
        """Remove a webhook subscription."""
        sub = db.query(WebhookSubscription).filter(WebhookSubscription.id == subscription_id).first()
        if not sub:
            return False
        db.delete(sub)
        db.commit()
        return True

    @classmethod
    def dispatch(cls, event: str, data: Dict[str, Any]):
        """
        Dispatch platform event to all matching active webhook subscriptions.
        Executed synchronously or in background tasks.
        """
        db = SessionLocal()
        try:
            subscriptions = db.query(WebhookSubscription).filter(
                WebhookSubscription.is_active == True
            ).all()

            matched = [
                s for s in subscriptions 
                if "*" in s.events or event in s.events or event.split(".")[0] + ".*" in s.events
            ]

            if not matched:
                return

            event_id = f"evt_{uuid.uuid4().hex[:12]}"
            timestamp = datetime.utcnow().isoformat() + "Z"
            envelope = {
                "id": event_id,
                "event": event,
                "timestamp": timestamp,
                "data": data,
            }
            payload_json = json.dumps(envelope, default=str)
            payload_bytes = payload_json.encode("utf-8")

            for sub in matched:
                cls._send_to_subscriber(db, sub, event, envelope, payload_bytes)

        except Exception as e:
            logger.error(f"Error in WebhookService.dispatch for event '{event}': {e}", exc_info=True)
        finally:
            db.close()

    @classmethod
    def _send_to_subscriber(
        cls,
        db: Session,
        subscription: WebhookSubscription,
        event: str,
        envelope: Dict[str, Any],
        payload_bytes: bytes,
    ):
        """Execute HTTP POST with signature to one subscriber."""
        signature = cls.generate_signature(payload_bytes, subscription.secret_key)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-Sales-CRM-Webhook/2.5",
            "X-CRM-Signature": signature,
            "X-CRM-Event": event,
            "X-CRM-Delivery-Id": envelope["id"],
            "X-CRM-Timestamp": envelope["timestamp"],
        }

        start_time = time.time()
        status_code = None
        success = False
        error_message = None

        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                res = client.post(subscription.target_url, content=payload_bytes, headers=headers)
                status_code = res.status_code
                latency_ms = round((time.time() - start_time) * 1000, 2)
                success = 200 <= status_code < 300

                if not success:
                    error_message = f"HTTP {status_code}: {res.text[:250]}"
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            error_message = str(e)[:300]
            logger.warning(f"Failed to deliver webhook {envelope['id']} to {subscription.target_url}: {e}")

        # Record delivery audit log
        delivery = WebhookDelivery(
            subscription_id=subscription.id,
            event=event,
            payload=envelope,
            status_code=status_code,
            success=success,
            error_message=error_message,
            latency_ms=latency_ms,
        )
        db.add(delivery)

        # Update subscription health
        subscription.last_delivery_at = datetime.utcnow()
        if success:
            subscription.failure_count = 0
            subscription.last_error = None
        else:
            subscription.failure_count += 1
            subscription.last_error = error_message

        db.commit()

    @classmethod
    def test_subscription(cls, db: Session, subscription_id: str) -> Dict[str, Any]:
        """Send a test ping event to verify subscriber endpoint connectivity."""
        sub = db.query(WebhookSubscription).filter(WebhookSubscription.id == subscription_id).first()
        if not sub:
            raise ValueError(f"Subscription '{subscription_id}' not found.")

        test_data = {
            "ping": "pong",
            "message": "Test webhook delivery from AI Sales & CRM OS",
            "test_lead": {
                "business_name": "Acme Dental Care",
                "email": "contact@acmedental.com",
                "phone": "+91 98765 43210",
                "city": "Lucknow",
            }
        }

        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        envelope = {
            "id": event_id,
            "event": "test.ping",
            "timestamp": timestamp,
            "data": test_data,
        }
        payload_bytes = json.dumps(envelope).encode("utf-8")
        cls._send_to_subscriber(db, sub, "test.ping", envelope, payload_bytes)

        # Return latest delivery log
        latest = db.query(WebhookDelivery).filter(
            WebhookDelivery.subscription_id == sub.id
        ).order_by(WebhookDelivery.created_at.desc()).first()

        return {
            "subscription_id": str(sub.id),
            "target_url": sub.target_url,
            "success": latest.success if latest else False,
            "status_code": latest.status_code if latest else None,
            "latency_ms": latest.latency_ms if latest else None,
            "error_message": latest.error_message if latest else None,
        }

    @classmethod
    def ingest_external_lead(cls, db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest a lead pushed from external PHP CRM, landing page, or form.
        Deduplicates, persists, and triggers outbound events.
        """
        business_name = payload.get("business_name") or payload.get("name")
        if not business_name:
            raise ValueError("Field 'business_name' is required.")

        email = (payload.get("email") or "").strip().lower() or None
        phone = (payload.get("phone") or "").strip() or None
        website = (payload.get("website") or "").strip() or None
        city = (payload.get("city") or "").strip() or None
        state = (payload.get("state") or "").strip() or None
        country = payload.get("country") or "India"
        source = payload.get("source_provider") or "external_crm_webhook"

        # Check for existing lead by website, phone, email, or name+city
        existing = None
        if website:
            existing = db.query(BusinessLead).filter(BusinessLead.website == website).first()

        if not existing and phone:
            phone_contact = db.query(LeadContact).filter(
                LeadContact.contact_type == ContactType.PHONE,
                (LeadContact.normalized_value == phone) | (LeadContact.original_value == phone)
            ).first()
            if phone_contact:
                existing = db.query(BusinessLead).filter(BusinessLead.id == phone_contact.lead_id).first()

        if not existing and email:
            email_contact = db.query(LeadContact).filter(
                LeadContact.contact_type == ContactType.EMAIL,
                (LeadContact.normalized_value == email) | (LeadContact.original_value == email)
            ).first()
            if email_contact:
                existing = db.query(BusinessLead).filter(BusinessLead.id == email_contact.lead_id).first()

        if not existing:
            existing = db.query(BusinessLead).filter(
                BusinessLead.business_name == business_name,
                BusinessLead.city == city,
            ).first()

        if existing:
            lead = existing
            if website and not lead.website:
                lead.website = website
            is_new = False
        else:
            lead = BusinessLead(
                business_name=business_name,
                category=payload.get("category") or "General Business",
                website=website,
                address=payload.get("address"),
                city=city,
                state=state,
                country=country,
                source_provider=source,
                provider_external_id=payload.get("external_id") or f"ext_{uuid.uuid4().hex[:8]}",
            )
            db.add(lead)
            db.flush()
            is_new = True

        # Attach email contact
        if email:
            has_contact = db.query(LeadContact).filter(
                LeadContact.lead_id == lead.id,
                LeadContact.contact_type == ContactType.EMAIL,
                (LeadContact.original_value == email) | (LeadContact.normalized_value == email),
            ).first()
            if not has_contact:
                db.add(LeadContact(
                    lead_id=lead.id,
                    contact_type=ContactType.EMAIL,
                    original_value=email,
                    normalized_value=email,
                    verification_status="verified" if payload.get("is_verified") else "unverified",
                    source_url=source,
                ))

        # Attach phone contact
        if phone:
            has_phone = db.query(LeadContact).filter(
                LeadContact.lead_id == lead.id,
                LeadContact.contact_type == ContactType.PHONE,
                (LeadContact.original_value == phone) | (LeadContact.normalized_value == phone),
            ).first()
            if not has_phone:
                db.add(LeadContact(
                    lead_id=lead.id,
                    contact_type=ContactType.PHONE,
                    original_value=phone,
                    normalized_value=phone,
                    verification_status="verified" if payload.get("is_verified") else "unverified",
                    source_url=source,
                ))

        db.commit()
        db.refresh(lead)

        resolved_email = lead.email or email
        resolved_phone = lead.phone or phone

        # Trigger outbound webhook dispatch
        event_name = "lead.discovered" if is_new else "lead.updated"
        cls.dispatch(event_name, {
            "lead_id": str(lead.id),
            "business_name": lead.business_name,
            "category": lead.category,
            "email": resolved_email,
            "phone": resolved_phone,
            "website": lead.website,
            "city": lead.city,
            "is_new": is_new,
            "source": source,
        })

        return {
            "success": True,
            "is_new": is_new,
            "lead_id": str(lead.id),
            "lead": {
                "id": str(lead.id),
                "business_name": lead.business_name,
                "email": resolved_email,
                "phone": resolved_phone,
                "website": lead.website,
                "city": lead.city,
                "created_at": lead.created_at.isoformat(),
            }
        }
