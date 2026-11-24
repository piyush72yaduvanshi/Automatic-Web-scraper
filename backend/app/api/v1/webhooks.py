"""Webhooks and External CRM Integration API Endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Header, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl

from app.core.database import get_db
from app.services.webhook_service import WebhookService
from app.models.webhook import WebhookSubscription, WebhookDelivery

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class CreateSubscriptionRequest(BaseModel):
    name: str
    target_url: str
    events: Optional[List[str]] = ["*"]
    secret_key: Optional[str] = None


class IngestLeadRequest(BaseModel):
    business_name: str
    category: Optional[str] = "General Business"
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    external_id: Optional[str] = None
    source_provider: Optional[str] = "external_crm"


class VerifySignatureRequest(BaseModel):
    payload: str
    signature: str
    secret_key: str


@router.post("/subscriptions")
def create_subscription(
    req: CreateSubscriptionRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Register a new outbound webhook subscription."""
    try:
        sub = WebhookService.create_subscription(
            db=db,
            name=req.name,
            target_url=req.target_url,
            events=req.events,
            secret_key=req.secret_key,
        )
        return {
            "success": True,
            "subscription": {
                "id": str(sub.id),
                "name": sub.name,
                "target_url": sub.target_url,
                "secret_key": sub.secret_key,
                "events": sub.events,
                "is_active": sub.is_active,
                "created_at": sub.created_at.isoformat(),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions")
def list_subscriptions(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List all registered webhook subscriptions."""
    subs = WebhookService.list_subscriptions(db=db, active_only=active_only)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "target_url": s.target_url,
            "secret_key": s.secret_key,
            "events": s.events,
            "is_active": s.is_active,
            "failure_count": s.failure_count,
            "last_delivery_at": s.last_delivery_at.isoformat() if s.last_delivery_at else None,
            "last_error": s.last_error,
            "created_at": s.created_at.isoformat(),
        }
        for s in subs
    ]


@router.delete("/subscriptions/{subscription_id}")
def delete_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Remove a webhook subscription."""
    deleted = WebhookService.delete_subscription(db=db, subscription_id=subscription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook subscription not found.")
    return {"success": True, "message": "Subscription deleted successfully."}


@router.post("/subscriptions/{subscription_id}/test")
def test_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Send an immediate test ping event to verify webhook URL connectivity."""
    try:
        return WebhookService.test_subscription(db=db, subscription_id=subscription_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deliveries")
def list_deliveries(
    limit: int = Query(50, ge=1, le=200),
    subscription_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Audit log of recent dispatched webhook events."""
    query = db.query(WebhookDelivery)
    if subscription_id:
        query = query.filter(WebhookDelivery.subscription_id == subscription_id)
    deliveries = query.order_by(WebhookDelivery.created_at.desc()).limit(limit).all()

    return [
        {
            "id": str(d.id),
            "subscription_id": str(d.subscription_id),
            "event": d.event,
            "payload": d.payload,
            "status_code": d.status_code,
            "success": d.success,
            "error_message": d.error_message,
            "latency_ms": d.latency_ms,
            "created_at": d.created_at.isoformat(),
        }
        for d in deliveries
    ]


@router.post("/ingest")
def ingest_lead_from_external_crm(
    req: IngestLeadRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Inbound webhook endpoint for external systems (e.g. PHP CRM, WordPress, forms)
    to ingest new leads into this AI Operating System.
    """
    try:
        return WebhookService.ingest_external_lead(db=db, payload=req.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest lead: {str(e)}")


@router.post("/verify")
def verify_signature(req: VerifySignatureRequest) -> Dict[str, Any]:
    """Helper endpoint to test and verify HMAC-SHA256 signatures."""
    valid = WebhookService.verify_signature(
        payload_bytes=req.payload.encode("utf-8"),
        signature_header=req.signature,
        secret_key=req.secret_key,
    )
    return {"valid": valid}
