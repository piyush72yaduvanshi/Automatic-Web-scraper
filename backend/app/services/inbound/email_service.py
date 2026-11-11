"""Email lead capture service."""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from email import message_from_bytes
from email.header import decode_header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.social_media_lead import InboundMessage
from app.models.business_lead import BusinessLead
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailLeadCaptureService:
    """Service for capturing leads from email replies."""
    
    # Interest signal keywords
    INTEREST_KEYWORDS = [
        "interested", "pricing", "demo", "meeting", "call", "quote",
        "proposal", "price", "cost", "schedule", "discuss", "learn more",
        "tell me more", "more information", "sign up", "get started"
    ]
    
    QUESTION_KEYWORDS = [
        "how", "what", "when", "where", "can you", "do you", "is it",
        "does it", "will it", "would you"
    ]
    
    OBJECTION_KEYWORDS = [
        "expensive", "too much", "budget", "not now", "maybe later",
        "not sure", "concerns", "worried"
    ]
    
    NEGATIVE_KEYWORDS = [
        "not interested", "no thanks", "stop", "unsubscribe", "remove",
        "spam", "never contact"
    ]
    
    @staticmethod
    def parse_incoming_email(email_data: bytes) -> Dict[str, Any]:
        """
        Parse raw email data.
        
        Args:
            email_data: Raw email bytes
            
        Returns:
            Dictionary with parsed email fields
        """
        msg = message_from_bytes(email_data)
        
        # Decode subject
        subject_header = msg.get("Subject", "")
        decoded_subject = ""
        if subject_header:
            for part, encoding in decode_header(subject_header):
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    decoded_subject += part
        
        # Extract sender
        from_header = msg.get("From", "")
        sender_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
        sender_email = sender_match.group(0) if sender_match else from_header
        
        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode(errors="ignore")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(errors="ignore")
        
        # Extract thread ID and message ID
        message_id = msg.get("Message-ID", "")
        in_reply_to = msg.get("In-Reply-To", "")
        references = msg.get("References", "")
        
        return {
            "sender_email": sender_email,
            "subject": decoded_subject,
            "body": body.strip(),
            "message_id": message_id,
            "in_reply_to": in_reply_to,
            "references": references,
            "received_at": datetime.utcnow(),
        }
    
    @classmethod
    def detect_interest_signals(cls, message_body: str, subject: str = "") -> Dict[str, Any]:
        """
        Detect interest signals in email content.
        
        Args:
            message_body: Email body text
            subject: Email subject
            
        Returns:
            Dictionary with classification, sentiment, and interest score
        """
        text = f"{subject} {message_body}".lower()
        
        # Count keyword matches
        interest_count = sum(1 for kw in cls.INTEREST_KEYWORDS if kw in text)
        question_count = sum(1 for kw in cls.QUESTION_KEYWORDS if kw in text)
        objection_count = sum(1 for kw in cls.OBJECTION_KEYWORDS if kw in text)
        negative_count = sum(1 for kw in cls.NEGATIVE_KEYWORDS if kw in text)
        
        # Determine classification
        if negative_count > 0:
            classification = "UNSUBSCRIBE" if "unsubscribe" in text or "stop" in text else "NOT_NOW"
            sentiment = "NEGATIVE"
            interest_score = 0.1
        elif interest_count >= 2:
            classification = "INTERESTED"
            sentiment = "INTERESTED"
            interest_score = 0.9
        elif interest_count == 1:
            classification = "INTERESTED"
            sentiment = "POSITIVE"
            interest_score = 0.7
        elif objection_count > 0:
            classification = "OBJECTION"
            sentiment = "NEUTRAL"
            interest_score = 0.4
        elif question_count > 0:
            classification = "QUESTION"
            sentiment = "POSITIVE"
            interest_score = 0.6
        else:
            classification = "NEUTRAL"
            sentiment = "NEUTRAL"
            interest_score = 0.5
        
        # Check for out-of-office
        ooo_patterns = ["out of office", "out of the office", "away from", "on vacation", "auto-reply", "automatic reply"]
        if any(pattern in text for pattern in ooo_patterns):
            classification = "OUT_OF_OFFICE"
            interest_score = 0.0
        
        return {
            "classification": classification,
            "sentiment": sentiment,
            "interest_score": interest_score,
            "requires_human_attention": classification in ["INTERESTED", "OBJECTION", "QUESTION"],
        }
    
    @classmethod
    async def create_lead_from_email(
        cls,
        email_data: Dict[str, Any],
        db: Session
    ) -> Optional[InboundMessage]:
        """
        Create inbound message and optionally business lead from email.
        
        Args:
            email_data: Parsed email data
            db: Database session
            
        Returns:
            Created InboundMessage or None
        """
        try:
            # Detect interest signals
            interest_signals = cls.detect_interest_signals(
                email_data.get("body", ""),
                email_data.get("subject", "")
            )
            
            # Create inbound message
            inbound_msg = InboundMessage(
                channel="EMAIL",
                sender_contact=email_data["sender_email"],
                message_body=email_data.get("body", ""),
                subject=email_data.get("subject"),
                interest_score=interest_signals["interest_score"],
                sentiment=interest_signals["sentiment"],
                classification=interest_signals["classification"],
                requires_human_attention=interest_signals["requires_human_attention"],
                thread_id=email_data.get("references", "").split()[0] if email_data.get("references") else None,
                in_reply_to_message_id=email_data.get("in_reply_to"),
                platform_message_id=email_data.get("message_id"),
                received_at=email_data.get("received_at", datetime.utcnow()),
                message_metadata={
                    "full_headers": email_data.get("headers", {}),
                },
                processed=False,
            )
            
            db.add(inbound_msg)
            db.commit()
            db.refresh(inbound_msg)
            
            logger.info(
                f"Created email inbound message: {inbound_msg.id} from {inbound_msg.sender_contact} "
                f"(classification: {inbound_msg.classification}, score: {inbound_msg.interest_score})"
            )
            
            # If high interest, convert to lead
            if interest_signals["interest_score"] >= 0.7:
                await cls._convert_to_business_lead(inbound_msg, db)
            
            return inbound_msg
            
        except IntegrityError as e:
            db.rollback()
            logger.debug(f"Duplicate email message: {e}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating email lead: {e}", exc_info=True)
            return None
    
    @classmethod
    async def _convert_to_business_lead(
        cls,
        inbound_msg: InboundMessage,
        db: Session
    ) -> Optional[BusinessLead]:
        """Convert inbound message to business lead."""
        
        # Check if lead already exists with this email
        existing_lead = db.query(BusinessLead).filter(
            BusinessLead.website.ilike(f"%{inbound_msg.sender_contact}%")
        ).first()
        
        if existing_lead:
            inbound_msg.lead_id = existing_lead.id
            inbound_msg.processed = True
            db.commit()
            return existing_lead
        
        # Extract domain from email
        domain = inbound_msg.sender_contact.split("@")[-1] if "@" in inbound_msg.sender_contact else ""
        
        # Create new business lead
        business_lead = BusinessLead(
            business_name=domain.split(".")[0].title() if domain else "Unknown",
            description=f"Lead from email reply: {inbound_msg.subject}",
            website=f"https://{domain}" if domain else None,
            source_provider="EMAIL_REPLY",
            provider_external_id=f"email_{inbound_msg.sender_contact}",
            status="discovered",
            lead_source="EMAIL_REPLY",
            qualification_score=inbound_msg.interest_score * 100,
            qualification_status="Interested" if inbound_msg.interest_score >= 0.7 else "New",
        )
        
        db.add(business_lead)
        db.commit()
        db.refresh(business_lead)
        
        # Link to inbound message
        inbound_msg.lead_id = business_lead.id
        inbound_msg.processed = True
        db.commit()
        
        logger.info(f"Converted email message {inbound_msg.id} to business lead {business_lead.id}")
        
        return business_lead
