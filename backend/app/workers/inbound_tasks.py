"""Celery tasks for processing inbound messages."""

import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.workers.celery_app import celery_app
from app.workers.tasks import DatabaseTask
from app.models.social_media_lead import InboundMessage, SocialMediaLead
from app.services.inbound.email_service import EmailLeadCaptureService
from app.services.social_capture.base_extractor import BaseSocialExtractor

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.inbound_tasks.process_inbound_messages",
    max_retries=3,
    default_retry_delay=120,
)
def process_inbound_messages(self):
    """Process unprocessed inbound messages every 2 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting inbound message processing")
        
        # Get unprocessed messages
        unprocessed_messages = db.query(InboundMessage).filter(
            and_(
                InboundMessage.processed == False,
                InboundMessage.interest_score >= 0.6  # Only process interested messages
            )
        ).limit(50).all()
        
        processed_count = 0
        error_count = 0
        
        for message in unprocessed_messages:
            try:
                # Convert high-interest messages to leads
                if message.interest_score >= 0.7 and not message.lead_id:
                    if message.channel == "EMAIL":
                        loop.run_until_complete(
                            EmailLeadCaptureService._convert_to_business_lead(message, db)
                        )
                    else:
                        # Handle WhatsApp/SMS conversion
                        from app.services.inbound.whatsapp_service import WhatsAppWebhookHandler
                        loop.run_until_complete(
                            WhatsAppWebhookHandler._convert_to_business_lead(message, db)
                        )
                    
                    processed_count += 1
                
                # Mark as processed if not requiring attention
                if not message.requires_human_attention:
                    message.processed = True
                    message.processed_at = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error processing message {message.id}: {e}")
                error_count += 1
        
        db.commit()
        
        logger.info(
            f"Inbound message processing completed: {processed_count} processed, "
            f"{error_count} errors"
        )
        
        return {
            "status": "success",
            "processed": processed_count,
            "errors": error_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in inbound message processing: {e}", exc_info=True)
        raise self.retry(exc=e)
    
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.inbound_tasks.process_social_media_leads",
    max_retries=3,
    default_retry_delay=180,
)
def process_social_media_leads(self):
    """Process unprocessed social media leads every 3 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting social media lead processing")
        
        # Get unprocessed social leads with high interest
        unprocessed_leads = db.query(SocialMediaLead).filter(
            and_(
                SocialMediaLead.processed == False,
                SocialMediaLead.interest_score >= 0.7
            )
        ).limit(50).all()
        
        converted_count = 0
        error_count = 0
        
        for social_lead in unprocessed_leads:
            try:
                # Convert to business lead if not already done
                if not social_lead.lead_id:
                    extractor = BaseSocialExtractor(social_lead.platform)
                    business_lead = loop.run_until_complete(
                        extractor.convert_to_business_lead(social_lead, db)
                    )
                    
                    if business_lead:
                        converted_count += 1
                else:
                    # Just mark as processed
                    social_lead.processed = True
                    db.commit()
            
            except Exception as e:
                logger.error(f"Error processing social lead {social_lead.id}: {e}")
                error_count += 1
        
        logger.info(
            f"Social lead processing completed: {converted_count} converted, "
            f"{error_count} errors"
        )
        
        return {
            "status": "success",
            "converted": converted_count,
            "errors": error_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in social lead processing: {e}", exc_info=True)
        raise self.retry(exc=e)
    
    finally:
        loop.close()
