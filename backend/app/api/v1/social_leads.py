"""API endpoints for social media lead capture and inbound messages."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.social_media_lead import SocialMediaLead, InboundMessage
from app.models.business_lead import BusinessLead
from app.schemas.social_media_lead import (
    SocialMediaLeadResponse,
    InboundMessageResponse,
    SocialLeadStats,
    InboundMessageStats,
    ManualSocialLeadCreate,
)
from app.services.inbound.whatsapp_service import WhatsAppWebhookHandler
from app.services.inbound.email_service import EmailLeadCaptureService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[SocialMediaLeadResponse])
async def list_social_leads(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    engagement_type: Optional[str] = Query(None, description="Filter by engagement type"),
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    min_interest_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum interest score"),
    days_back: int = Query(7, ge=1, le=90, description="Days to look back"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    """
    List social media captured leads with filters.
    
    **Authentication**: Requires valid API key
    """
    # Build query
    query = db.query(SocialMediaLead)
    
    # Apply filters
    since_date = datetime.utcnow() - timedelta(days=days_back)
    query = query.filter(SocialMediaLead.engagement_timestamp >= since_date)
    
    if platform:
        query = query.filter(SocialMediaLead.platform == platform.upper())
    
    if engagement_type:
        query = query.filter(SocialMediaLead.engagement_type == engagement_type.upper())
    
    if processed is not None:
        query = query.filter(SocialMediaLead.processed == processed)
    
    if min_interest_score is not None:
        query = query.filter(SocialMediaLead.interest_score >= min_interest_score)
    
    # Order by most recent first
    query = query.order_by(desc(SocialMediaLead.engagement_timestamp))
    
    # Paginate
    total = query.count()
    leads = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(leads)} social leads (total: {total})")
    
    return leads


@router.get("/stats", response_model=SocialLeadStats)
async def get_social_lead_stats(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    """
    Get statistics for social lead capture.
    
    **Authentication**: Requires valid API key
    """
    since_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Total engagements
    total_engagements = db.query(func.count(SocialMediaLead.id)).filter(
        SocialMediaLead.engagement_timestamp >= since_date
    ).scalar() or 0
    
    # By platform
    by_platform_query = db.query(
        SocialMediaLead.platform,
        func.count(SocialMediaLead.id)
    ).filter(
        SocialMediaLead.engagement_timestamp >= since_date
    ).group_by(SocialMediaLead.platform).all()
    
    by_platform = {platform: count for platform, count in by_platform_query}
    
    # By engagement type
    by_type_query = db.query(
        SocialMediaLead.engagement_type,
        func.count(SocialMediaLead.id)
    ).filter(
        SocialMediaLead.engagement_timestamp >= since_date
    ).group_by(SocialMediaLead.engagement_type).all()
    
    by_engagement_type = {eng_type: count for eng_type, count in by_type_query}
    
    # Processed counts
    processed_count = db.query(func.count(SocialMediaLead.id)).filter(
        and_(
            SocialMediaLead.engagement_timestamp >= since_date,
            SocialMediaLead.processed == True
        )
    ).scalar() or 0
    
    unprocessed_count = total_engagements - processed_count
    
    # Converted to leads
    converted_to_leads = db.query(func.count(SocialMediaLead.id)).filter(
        and_(
            SocialMediaLead.engagement_timestamp >= since_date,
            SocialMediaLead.lead_id.isnot(None)
        )
    ).scalar() or 0
    
    # Average interest score
    avg_score = db.query(func.avg(SocialMediaLead.interest_score)).filter(
        SocialMediaLead.engagement_timestamp >= since_date
    ).scalar() or 0.5
    
    # Last captured
    last_captured = db.query(func.max(SocialMediaLead.engagement_timestamp)).filter(
        SocialMediaLead.engagement_timestamp >= since_date
    ).scalar()
    
    return SocialLeadStats(
        total_engagements=total_engagements,
        by_platform=by_platform,
        by_engagement_type=by_engagement_type,
        processed_count=processed_count,
        unprocessed_count=unprocessed_count,
        converted_to_leads=converted_to_leads,
        average_interest_score=float(avg_score),
        last_captured_at=last_captured,
    )


@router.post("/manual", response_model=SocialMediaLeadResponse)
async def create_manual_social_lead(
    lead_data: ManualSocialLeadCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    """
    Manually create a social media lead.
    
    **Authentication**: Requires valid API key
    """
    social_lead = SocialMediaLead(
        platform=lead_data.platform.upper(),
        social_username=lead_data.social_username,
        social_profile_url=lead_data.social_profile_url,
        message_content=lead_data.message_content,
        engagement_type=lead_data.engagement_type.upper(),
        processing_notes=lead_data.notes,
        engagement_timestamp=datetime.utcnow(),
        interest_score=0.5,
        sentiment="NEUTRAL",
        processed=False,
    )
    
    db.add(social_lead)
    db.commit()
    db.refresh(social_lead)
    
    logger.info(f"Manually created social lead: {social_lead.id}")
    
    return social_lead


@router.get("/inbound-messages", response_model=List[InboundMessageResponse])
async def list_inbound_messages(
    channel: Optional[str] = Query(None, description="Filter by channel"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    processed: Optional[bool] = Query(None, description="Filter by processed status"),
    requires_attention: Optional[bool] = Query(None, description="Filter by attention required"),
    days_back: int = Query(7, ge=1, le=90),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    """
    List inbound messages with filters.
    
    **Authentication**: Requires valid API key
    """
    query = db.query(InboundMessage)
    
    # Apply filters
    since_date = datetime.utcnow() - timedelta(days=days_back)
    query = query.filter(InboundMessage.received_at >= since_date)
    
    if channel:
        query = query.filter(InboundMessage.channel == channel.upper())
    
    if classification:
        query = query.filter(InboundMessage.classification == classification.upper())
    
    if processed is not None:
        query = query.filter(InboundMessage.processed == processed)
    
    if requires_attention is not None:
        query = query.filter(InboundMessage.requires_human_attention == requires_attention)
    
    # Order by most recent first
    query = query.order_by(desc(InboundMessage.received_at))
    
    # Paginate
    total = query.count()
    messages = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(messages)} inbound messages (total: {total})")
    
    return messages


@router.get("/inbound-messages/stats", response_model=InboundMessageStats)
async def get_inbound_message_stats(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    """
    Get statistics for inbound messages.
    
    **Authentication**: Requires valid API key
    """
    since_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Total messages
    total_messages = db.query(func.count(InboundMessage.id)).filter(
        InboundMessage.received_at >= since_date
    ).scalar() or 0
    
    # By channel
    by_channel_query = db.query(
        InboundMessage.channel,
        func.count(InboundMessage.id)
    ).filter(
        InboundMessage.received_at >= since_date
    ).group_by(InboundMessage.channel).all()
    
    by_channel = {channel: count for channel, count in by_channel_query}
    
    # By classification
    by_classification_query = db.query(
        InboundMessage.classification,
        func.count(InboundMessage.id)
    ).filter(
        InboundMessage.received_at >= since_date
    ).group_by(InboundMessage.classification).all()
    
    by_classification = {cls: count for cls, count in by_classification_query if cls}
    
    # Processed count
    processed_count = db.query(func.count(InboundMessage.id)).filter(
        and_(
            InboundMessage.received_at >= since_date,
            InboundMessage.processed == True
        )
    ).scalar() or 0
    
    # Requires attention
    requires_attention_count = db.query(func.count(InboundMessage.id)).filter(
        and_(
            InboundMessage.received_at >= since_date,
            InboundMessage.requires_human_attention == True
        )
    ).scalar() or 0
    
    # Average interest score
    avg_score = db.query(func.avg(InboundMessage.interest_score)).filter(
        InboundMessage.received_at >= since_date
    ).scalar() or 0.5
    
    # Last received
    last_received = db.query(func.max(InboundMessage.received_at)).filter(
        InboundMessage.received_at >= since_date
    ).scalar()
    
    return InboundMessageStats(
        total_messages=total_messages,
        by_channel=by_channel,
        by_classification=by_classification,
        processed_count=processed_count,
        requires_attention_count=requires_attention_count,
        average_interest_score=float(avg_score),
        last_received_at=last_received,
    )


# Webhook endpoints
@router.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    request: Request,
):
    """
    WhatsApp webhook verification endpoint.
    
    **No authentication required** - Meta verification endpoint
    """
    # Get query parameters
    hub_mode = request.query_params.get("hub.mode")
    hub_verify_token = request.query_params.get("hub.verify_token")
    hub_challenge = request.query_params.get("hub.challenge")
    
    from app.core.config import settings
    verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "default_verify_token")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge)
    else:
        logger.warning(f"WhatsApp webhook verification failed: mode={hub_mode}")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/whatsapp")
async def handle_whatsapp_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    WhatsApp webhook receiver.
    
    **No API key authentication** - validates webhook signature instead
    """
    try:
        # Get request body
        body = await request.body()
        body_str = body.decode("utf-8")
        
        # Validate signature
        if x_hub_signature_256:
            if not WhatsAppWebhookHandler.validate_webhook_signature(body_str, x_hub_signature_256):
                logger.warning("Invalid WhatsApp webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON
        payload = await request.json()
        
        # Extract message data
        message_data = WhatsAppWebhookHandler.extract_phone_and_message(payload)
        
        if message_data:
            # Create inbound message and lead
            inbound_msg = await WhatsAppWebhookHandler.create_lead_from_whatsapp(
                message_data, db
            )
            
            if inbound_msg:
                logger.info(f"WhatsApp message processed: {inbound_msg.id}")
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/webhooks/email")
async def handle_email_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Email webhook receiver (SendGrid/Mailgun format).
    
    **No API key authentication** - validates webhook signature
    """
    try:
        # Parse email payload (SendGrid format)
        payload = await request.json()
        
        # Process each email in the batch
        for email_data in payload:
            # Extract email fields (adjust based on provider)
            sender_email = email_data.get("from", "")
            subject = email_data.get("subject", "")
            body = email_data.get("text", "") or email_data.get("html", "")
            
            parsed_email = {
                "sender_email": sender_email,
                "subject": subject,
                "body": body,
                "message_id": email_data.get("message-id", ""),
                "in_reply_to": email_data.get("in-reply-to", ""),
                "references": email_data.get("references", ""),
                "received_at": datetime.utcnow(),
            }
            
            # Create inbound message
            inbound_msg = await EmailLeadCaptureService.create_lead_from_email(
                parsed_email, db
            )
            
            if inbound_msg:
                logger.info(f"Email webhook processed: {inbound_msg.id}")
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
