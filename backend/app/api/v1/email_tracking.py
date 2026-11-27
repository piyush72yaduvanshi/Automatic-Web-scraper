"""Email Open & Personalized Image Tracking Router.

Provides:
1. 1x1 Transparent PNG pixel tracking for email opens.
2. Personalized dynamic image asset tracking and streaming.
3. Direct SMTP outbound email dispatch with auto-injected tracking.
4. On-demand IMAP inbound reply polling and auto-stop sequence triggers.
5. Email outreach metrics and engagement statistics.
"""

from fastapi import APIRouter, Depends, Query, Request, Response, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.crm import Email, Activity, Contact, Company
from app.providers.communication.smtp_provider import SMTPProvider
from app.services.imap_reply_tracker import IMAPReplyTrackerService
from app.services.webhook_service import WebhookService
from app.services.storage_service import MinIOStorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-tracking", tags=["Email Tracking & SMTP/IMAP"])

# 1x1 Transparent PNG bytes (RFC-compliant PNG datastream)
TRANSPARENT_1X1_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00"
    b"\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class SMTPSendRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body_html: str
    body_text: Optional[str] = None
    from_email: Optional[str] = None
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    personalized_image_url: Optional[str] = None


def _record_email_open(token: str, request: Request, db: Session) -> Optional[Email]:
    """Helper to update email open metrics and dispatch real-time events."""
    if not token:
        return None
    try:
        email_record = db.query(Email).filter(Email.tracking_token == token).first()
        if not email_record:
            return None

        now = datetime.utcnow()
        is_first_open = email_record.opened_at is None

        if is_first_open:
            email_record.opened_at = now
            if email_record.status in ("draft", "sent", "delivered"):
                email_record.status = "opened"

        email_record.open_count = (email_record.open_count or 0) + 1
        db.flush()

        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        activity = Activity(
            contact_id=email_record.contact_id,
            company_id=email_record.company_id,
            deal_id=email_record.deal_id,
            activity_type="EMAIL",
            title=f"Email Opened: '{email_record.subject or 'Cold Outreach'}'",
            description=f"Open #{email_record.open_count} | IP: {client_ip} | UA: {user_agent[:120]}",
            created_at=now,
        )
        db.add(activity)
        db.commit()

        # Dispatch real-time outbound webhook
        try:
            WebhookService.dispatch("email.opened", {
                "email_id": str(email_record.id),
                "tracking_token": token,
                "to_email": email_record.to_email,
                "subject": email_record.subject,
                "opened_at": now.isoformat(),
                "open_count": email_record.open_count,
                "client_ip": client_ip,
                "is_first_open": is_first_open,
            })
        except Exception as we:
            logger.warning(f"Failed to dispatch email.opened webhook: {we}")

        return email_record
    except Exception as e:
        logger.error(f"Error recording email open for token {token}: {e}")
        db.rollback()
        return None


@router.get("/open/{tracking_token}.png")
async def track_email_open(
    tracking_token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    1x1 Transparent Tracking Pixel.
    Tracks email open timestamp, increments open count, creates CRM activity,
    and dispatches 'email.opened' webhook event.
    Always returns valid 1x1 PNG with zero caching headers.
    """
    _record_email_open(tracking_token, request, db)

    return Response(
        content=TRANSPARENT_1X1_PNG,
        media_type="image/png",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0, post-check=0, pre-check=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/image/{asset_id}")
async def serve_personalized_image(
    asset_id: str,
    request: Request,
    token: Optional[str] = Query(None, description="Optional email tracking token"),
    db: Session = Depends(get_db),
):
    """
    Serves a personalized image banner or asset stored in MinIO/local storage,
    while recording the email open event if a tracking token is present.
    """
    if token:
        _record_email_open(token, request, db)

    # 1. Attempt retrieval from MinIO / local storage
    file_bytes = MinIOStorageService.download_bytes(asset_id)
    if file_bytes:
        media_type = "image/png"
        if asset_id.endswith(".svg"):
            media_type = "image/svg+xml"
        elif asset_id.endswith(".jpg") or asset_id.endswith(".jpeg"):
            media_type = "image/jpeg"
        elif asset_id.endswith(".webp"):
            media_type = "image/webp"

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )

    # 2. Dynamic high-res fallback SVG banner if asset not found in MinIO
    fallback_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200" viewBox="0 0 600 200">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#8b5cf6"/>
    </linearGradient>
  </defs>
  <rect width="600" height="200" rx="16" fill="url(#bg)" stroke="#334155" stroke-width="2"/>
  <rect x="24" y="24" width="8" height="152" rx="4" fill="url(#accent)"/>
  <text x="48" y="70" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="700" fill="#f8fafc">
    Customized Solution Proposal
  </text>
  <text x="48" y="105" font-family="system-ui, -apple-system, sans-serif" font-size="14" fill="#94a3b8">
    Tailored Growth Architecture &amp; Autonomous Lead Generation
  </text>
  <text x="48" y="150" font-family="system-ui, -apple-system, sans-serif" font-size="12" font-weight="600" fill="#38bdf8">
    AI SALES &amp; CRM OPERATING SYSTEM - VERIFIED ASSET
  </text>
</svg>"""

    return Response(
        content=fallback_svg.encode("utf-8"),
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@router.post("/send-smtp")
async def send_smtp_email(
    req: SMTPSendRequest,
    db: Session = Depends(get_db),
):
    """
    Sends an outbound cold outreach email via SMTP, embeds tracking pixel & personalized image,
    persists record to CRM `emails` table, and returns tracking identifiers.
    """
    token = SMTPProvider.generate_tracking_token()
    message_id = SMTPProvider.generate_message_id()

    # Create email record
    email_obj = Email(
        id=uuid.uuid4(),
        contact_id=uuid.UUID(req.contact_id) if req.contact_id else None,
        company_id=uuid.UUID(req.company_id) if req.company_id else None,
        subject=req.subject,
        to_email=str(req.to_email),
        from_email=req.from_email or settings.SMTP_FROM_EMAIL or "outreach@crm.internal",
        sent_message_id=message_id,
        tracking_token=token,
        body_html=req.body_html,
        body_text=req.body_text or "Please view this email in an HTML-compatible client.",
        direction="OUTBOUND",
        status="sent",
        sent_at=datetime.utcnow(),
    )
    db.add(email_obj)
    db.commit()
    db.refresh(email_obj)

    # Deliver via SMTP provider
    send_result = SMTPProvider.send_email(
        to_email=str(req.to_email),
        subject=req.subject,
        body_html=req.body_html,
        body_text=req.body_text,
        from_email=email_obj.from_email,
        tracking_token=token,
        personalized_image_url=req.personalized_image_url,
    )

    base_url = settings.TRACKING_BASE_URL.rstrip("/")
    tracking_pixel_url = f"{base_url}/api/v1/email-tracking/open/{token}.png"

    return {
        "success": send_result.get("success", False),
        "mode": send_result.get("mode"),
        "email_id": str(email_obj.id),
        "sent_message_id": message_id,
        "tracking_token": token,
        "tracking_pixel_url": tracking_pixel_url,
        "recipient": str(req.to_email),
        "subject": req.subject,
        "sent_at": email_obj.sent_at.isoformat(),
    }


@router.post("/poll-replies")
async def poll_imap_replies(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Manually triggers IMAP polling to detect inbound prospect replies,
    matches them against sent outreach campaigns, executes AI categorization,
    applies stop conditions, and emits real-time webhooks.
    """
    res = await IMAPReplyTrackerService.poll_replies(db=db, limit=limit)
    return res


@router.get("/stats")
def get_email_tracking_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated outreach deliverability and engagement statistics.
    """
    total_sent = db.query(Email).filter(Email.direction == "OUTBOUND").count()
    total_opened = db.query(Email).filter(Email.opened_at.isnot(None)).count()
    total_replied = db.query(Email).filter(Email.replied_at.isnot(None)).count()
    total_open_events = db.query(func.sum(Email.open_count)).scalar() or 0

    open_rate = round((total_opened / total_sent * 100), 2) if total_sent > 0 else 0.0
    reply_rate = round((total_replied / total_sent * 100), 2) if total_sent > 0 else 0.0

    return {
        "total_sent": total_sent,
        "total_opened": total_opened,
        "total_open_events": total_open_events,
        "total_replied": total_replied,
        "open_rate_percent": open_rate,
        "reply_rate_percent": reply_rate,
        "smtp_configured": SMTPProvider.is_configured(),
        "imap_configured": IMAPReplyTrackerService.is_configured(),
    }
