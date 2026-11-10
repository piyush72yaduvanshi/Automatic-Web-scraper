"""Outreach, Campaigns, Approval Queue, Suppression, and Conversation Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid

from app.core.database import get_db
from app.core.security import verify_api_key
from app.core.rate_limiter import limiter
from app.core.config import settings
from app.services.outreach_service import OutreachService
from app.providers.communication.whatsapp_provider import WhatsAppProvider

router = APIRouter(prefix="/outreach", tags=["outreach"])


# -------------------------------------------------------------
# Human Approval Queue
# -------------------------------------------------------------
@router.get("/approvals")
def list_approvals(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List pending or executed outreach approvals."""
    approvals = OutreachService.list_approvals(db, status)
    return [
        {
            "id": str(a.id),
            "action_type": a.action_type,
            "recipient_name": a.recipient_name,
            "recipient_destination": a.recipient_destination,
            "subject": a.subject,
            "body_content": a.body_content,
            "evidence_context": a.evidence_context,
            "status": a.status,
            "rejection_reason": a.rejection_reason,
            "error_message": a.error_message,
            "created_at": a.created_at.isoformat(),
            "sent_at": a.sent_at.isoformat() if a.sent_at else None,
        }
        for a in approvals
    ]


@router.post("/approvals/{approval_id}/approve")
@limiter.limit(settings.RATE_LIMIT_OUTREACH)
async def approve_outreach(
    request: Request,
    approval_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Explicitly approve and execute outbound email or message."""
    try:
        return await OutreachService.approve_and_send(approval_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/approvals/{approval_id}/reject")
@limiter.limit(settings.RATE_LIMIT_OUTREACH)
def reject_outreach(
    request: Request,
    approval_id: str,
    reason: str = Body("Rejected by user review", embed=True),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Reject an outreach item, preventing sending."""
    try:
        appr = OutreachService.reject_approval(approval_id, reason, db)
        return {"id": str(appr.id), "status": appr.status, "reason": appr.rejection_reason}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/approvals/{approval_id}")
def edit_outreach_draft(
    approval_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Edit subject or content of a pending approval item."""
    try:
        appr = OutreachService.edit_approval(
            approval_id=approval_id,
            new_subject=payload.get("subject"),
            new_body=payload.get("body_content", ""),
            db=db,
        )
        return {"id": str(appr.id), "status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/drafts/lead/{lead_id}")
@limiter.limit(settings.RATE_LIMIT_OUTREACH)
async def generate_lead_draft(
    request: Request,
    lead_id: str,
    channel: str = Query("EMAIL"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """AI drafts a personalized cold message and enqueues to the PENDING approval queue."""
    try:
        approval = await OutreachService.prepare_outreach_draft_for_lead(lead_id, channel, db)
        return {
            "message": "Outreach draft prepared and enqueued for human review.",
            "approval_id": str(approval.id),
            "recipient": approval.recipient_destination,
            "status": approval.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------------------------------------------------
# Campaigns
# -------------------------------------------------------------
@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    campaigns = OutreachService.list_campaigns(db)
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "channel": c.channel,
            "status": c.status,
            "total_prospects": c.total_prospects,
            "sent_count": c.sent_count,
            "replied_count": c.replied_count,
            "steps_count": len(c.steps),
            "created_at": c.created_at.isoformat(),
        }
        for c in campaigns
    ]


@router.post("/campaigns")
def create_campaign(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    camp = OutreachService.create_campaign(data, db)
    return {"id": str(camp.id), "name": camp.name, "status": "created"}


# -------------------------------------------------------------
# Suppression Registry
# -------------------------------------------------------------
@router.get("/suppression")
def list_suppression(db: Session = Depends(get_db)):
    records = OutreachService.list_suppression(db)
    return [
        {
            "id": str(s.id),
            "recipient": s.recipient,
            "channel": s.channel,
            "reason": s.reason,
            "opted_out_at": s.opted_out_at.isoformat(),
        }
        for s in records
    ]


@router.post("/suppression")
def add_suppression(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    recipient = data.get("recipient")
    if not recipient:
        raise HTTPException(status_code=400, detail="recipient is required")
    s = OutreachService.add_to_suppression(
        recipient=recipient,
        channel=data.get("channel", "ALL"),
        reason=data.get("reason", "MANUAL"),
        db=db,
    )
    return {"id": str(s.id), "recipient": s.recipient, "status": "suppressed"}


# -------------------------------------------------------------
# Conversations
# -------------------------------------------------------------
@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    convs = OutreachService.list_conversations(db)
    return [
        {
            "id": str(cv.id),
            "channel": cv.channel,
            "subject": cv.subject,
            "status": cv.status,
            "last_message_at": cv.last_message_at.isoformat(),
            "messages_count": len(cv.messages),
        }
        for cv in convs
    ]


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: str, db: Session = Depends(get_db)):
    cv = OutreachService.get_conversation(conv_id, db)
    if not cv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": str(cv.id),
        "channel": cv.channel,
        "subject": cv.subject,
        "status": cv.status,
        "messages": [
            {
                "id": str(m.id),
                "direction": m.direction,
                "sender": m.sender,
                "recipient": m.recipient,
                "body": m.body,
                "delivery_status": m.delivery_status,
                "ai_classification": m.ai_classification,
                "suggested_reply": m.suggested_reply,
                "created_at": m.created_at.isoformat(),
            }
            for m in cv.messages
        ],
    }


@router.post("/conversations/{conv_id}/messages")
async def send_or_receive_message(
    conv_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """
    Post a message to a conversation.
    If direction is INBOUND, runs ReplyIntelligenceService (11 intent categories + stop conditions).
    """
    direction = payload.get("direction", "INBOUND").upper()
    body_text = payload.get("body", "")
    sender = payload.get("sender", "prospect@example.com")

    if direction == "INBOUND":
        from app.services.reply_intelligence_service import ReplyIntelligenceService
        return await ReplyIntelligenceService.process_incoming_message(
            conversation_id=conv_id,
            sender=sender,
            body_text=body_text,
            db=db,
        )
    else:
        # Outbound message via approval queue
        approval = OutreachService.stage_outreach_draft(
            recipient=payload.get("recipient", sender),
            subject=payload.get("subject", "Reply"),
            body=body_text,
            channel="EMAIL",
            db=db,
        )
        return {"status": "staged_for_approval", "approval_id": str(approval.id)}


# -------------------------------------------------------------
# WhatsApp Webhook
# -------------------------------------------------------------
@router.get("/webhook/whatsapp")
def verify_whatsapp_webhook(request: Request):
    """Verification handshake endpoint for Meta WhatsApp Cloud API."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    from app.core.config import settings
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(challenge) if challenge and challenge.isdigit() else challenge
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook/whatsapp")
async def handle_whatsapp_webhook(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Ingest inbound WhatsApp messages, trigger AI classification, and handle opt-outs."""
    events = WhatsAppProvider.process_webhook_payload(payload)
    for ev in events:
        sender_phone = ev["sender_phone"]
        body_text = ev["body"]

        # Check opt-out
        if ev.get("is_opt_out"):
            OutreachService.add_to_suppression(
                recipient=sender_phone,
                channel="WHATSAPP",
                reason="UNSUBSCRIBE",
                db=db,
            )
            continue

        # Inbound conversation logging
        from app.models.outreach import Conversation, ConversationMessage
        conv = db.query(Conversation).filter(
            Conversation.channel == "WHATSAPP",
            Conversation.subject == f"WhatsApp: {sender_phone}",
        ).first()

        if not conv:
            conv = Conversation(
                channel="WHATSAPP",
                subject=f"WhatsApp: {sender_phone}",
                status="ACTIVE",
            )
            db.add(conv)
            db.flush()

        msg = ConversationMessage(
            conversation_id=conv.id,
            direction="INBOUND",
            sender=sender_phone,
            recipient="me",
            body=body_text,
            delivery_status="delivered",
        )
        db.add(msg)
        conv.last_message_at = datetime.utcnow()
        db.commit()

    return {"status": "processed", "events_count": len(events)}

