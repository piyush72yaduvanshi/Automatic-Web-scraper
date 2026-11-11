"""WhatsApp webhook handler service."""

import logging
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.social_media_lead import InboundMessage
from app.models.business_lead import BusinessLead
from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppWebhookHandler:
    """Handler for WhatsApp Business API webhooks."""
    
    @staticmethod
    def validate_webhook_signature(payload: str, signature: str) -> bool:
        """
        Validate WhatsApp webhook signature.
        
        Args:
            payload: Request body as string
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        app_secret = getattr(settings, "WHATSAPP_APP_SECRET", None)
        
        if not app_secret:
            logger.warning("WhatsApp app secret not configured")
            return False
        
        if not signature or not signature.startswith("sha256="):
            return False
        
        # Calculate expected signature
        expected_signature = hmac.new(
            app_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant time comparison)
        received_signature = signature.replace("sha256=", "")
        return hmac.compare_digest(expected_signature, received_signature)
    
    @staticmethod
    def extract_phone_and_message(webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract phone number and message from WhatsApp webhook payload.
        
        Args:
            webhook_data: Webhook JSON payload
            
        Returns:
            Dictionary with phone, message, name, and metadata
        """
        try:
            entry = webhook_data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            contacts = value.get("contacts", [])
            contact = contacts[0] if contacts else {}
            
            return {
                "phone": message.get("from", ""),
                "message": message.get("text", {}).get("body", ""),
                "name": contact.get("profile", {}).get("name", "Unknown"),
                "message_id": message.get("id", ""),
                "timestamp": int(message.get("timestamp", 0)),
                "raw_data": message,
            }
        
        except (IndexError, KeyError) as e:
            logger.error(f"Error parsing WhatsApp webhook: {e}")
            return None
    
    @classmethod
    def classify_whatsapp_message(cls, message_text: str) -> Dict[str, Any]:
        """
        Classify WhatsApp message intent.
        
        Args:
            message_text: Message content
            
        Returns:
            Dictionary with classification, sentiment, and interest score
        """
        text_lower = message_text.lower()
        
        # Check for opt-out
        if any(word in text_lower for word in ["stop", "unsubscribe", "remove me"]):
            return {
                "classification": "UNSUBSCRIBE",
                "sentiment": "NEGATIVE",
                "interest_score": 0.0,
                "requires_human_attention": True,
            }
        
        # Check for high interest
        high_interest = ["interested", "yes", "pricing", "cost", "demo", "call me", "contact me"]
        if any(word in text_lower for word in high_interest):
            return {
                "classification": "INTERESTED",
                "sentiment": "INTERESTED",
                "interest_score": 0.9,
                "requires_human_attention": True,
            }
        
        # Check for questions
        question_words = ["how", "what", "when", "where", "can you", "do you"]
        if any(word in text_lower for word in question_words) or "?" in message_text:
            return {
                "classification": "QUESTION",
                "sentiment": "POSITIVE",
                "interest_score": 0.6,
                "requires_human_attention": True,
            }
        
        # Default
        return {
            "classification": "NEUTRAL",
            "sentiment": "NEUTRAL",
            "interest_score": 0.5,
            "requires_human_attention": False,
        }
    
    @classmethod
    async def create_lead_from_whatsapp(
        cls,
        message_data: Dict[str, Any],
        db: Session
    ) -> Optional[InboundMessage]:
        """
        Create inbound message and optionally business lead from WhatsApp message.
        
        Args:
            message_data: Extracted WhatsApp message data
            db: Database session
            
        Returns:
            Created InboundMessage or None
        """
        try:
            # Classify message
            classification = cls.classify_whatsapp_message(message_data["message"])
            
            # Create inbound message
            inbound_msg = InboundMessage(
                channel="WHATSAPP",
                sender_contact=message_data["phone"],
                message_body=message_data["message"],
                interest_score=classification["interest_score"],
                sentiment=classification["sentiment"],
                classification=classification["classification"],
                requires_human_attention=classification["requires_human_attention"],
                platform_message_id=message_data["message_id"],
                received_at=datetime.fromtimestamp(message_data["timestamp"]) if message_data["timestamp"] else datetime.utcnow(),
                message_metadata={
                    "sender_name": message_data.get("name"),
                    "raw_data": message_data.get("raw_data"),
                },
                processed=False,
            )
            
            db.add(inbound_msg)
            db.commit()
            db.refresh(inbound_msg)
            
            logger.info(
                f"Created WhatsApp inbound message: {inbound_msg.id} from {inbound_msg.sender_contact} "
                f"(classification: {inbound_msg.classification}, score: {inbound_msg.interest_score})"
            )
            
            # If high interest, convert to lead
            if classification["interest_score"] >= 0.7:
                await cls._convert_to_business_lead(inbound_msg, db)
            
            return inbound_msg
            
        except IntegrityError as e:
            db.rollback()
            logger.debug(f"Duplicate WhatsApp message: {e}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating WhatsApp lead: {e}", exc_info=True)
            return None
    
    @classmethod
    async def _convert_to_business_lead(
        cls,
        inbound_msg: InboundMessage,
        db: Session
    ) -> Optional[BusinessLead]:
        """Convert WhatsApp message to business lead."""
        
        # Check if lead already exists with this phone
        existing_lead = db.query(BusinessLead).filter(
            BusinessLead.provider_external_id == f"whatsapp_{inbound_msg.sender_contact}"
        ).first()
        
        if existing_lead:
            inbound_msg.lead_id = existing_lead.id
            inbound_msg.processed = True
            db.commit()
            return existing_lead
        
        # Get sender name from metadata
        sender_name = inbound_msg.message_metadata.get("sender_name", "Unknown") if inbound_msg.message_metadata else "Unknown"
        
        # Create new business lead
        business_lead = BusinessLead(
            business_name=sender_name,
            description=f"Lead from WhatsApp: {inbound_msg.message_body[:200]}",
            source_provider="WHATSAPP",
            provider_external_id=f"whatsapp_{inbound_msg.sender_contact}",
            status="discovered",
            lead_source="WHATSAPP",
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
        
        logger.info(f"Converted WhatsApp message {inbound_msg.id} to business lead {business_lead.id}")
        
        return business_lead
