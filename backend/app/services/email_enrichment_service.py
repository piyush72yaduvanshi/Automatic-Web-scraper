"""Email discovery and enrichment for leads without contact information."""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType
import uuid

logger = logging.getLogger(__name__)


class EmailEnrichmentService:
    """Discovers and validates email addresses for leads."""
    
    @classmethod
    async def enrich_lead_email(cls, lead_id: str, db: Session) -> Dict[str, Any]:
        """
        Find and validate email for a lead using:
        1. Website scraping (existing MultiSourceEnricher)
        2. Pattern guessing (firstname.lastname@domain.com, info@, contact@)
        3. External API (Hunter.io/Apollo if API key available)
        """
        lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(str(lead_id))).first()
        if not lead:
            return {"success": False, "error": "Lead not found"}
        
        # Check if email already exists
        existing_email = db.query(LeadContact).filter(
            LeadContact.lead_id == lead_id,
            LeadContact.contact_type == ContactType.EMAIL
        ).first()
        
        if existing_email:
            lead.email_enrichment_status = 'not_needed'
            db.commit()
            return {"success": True, "email": existing_email.normalized_value, "source": "existing"}
        
        discovered_emails = []
        
        # Strategy 1: Use existing enrichment service (website scraping)
        if lead.website:
            try:
                from app.providers.enrichment.multi_source_enricher import MultiSourceEnricher
                enricher = MultiSourceEnricher()
                result = await enricher.enrich_lead(
                    business_name=lead.business_name,
                    website=lead.website,
                    category=lead.category,
                    city=lead.city,
                    state=lead.state
                )
                
                for email_data in result.get("emails", []):
                    discovered_emails.append({
                        "email": email_data.get("email"),
                        "source": "website_scraping",
                        "confidence": "medium"
                    })
            except Exception as e:
                logger.warning(f"Website scraping failed for lead {lead_id}: {e}")
        
        # Strategy 2: Pattern guessing
        if lead.website and not discovered_emails:
            from urllib.parse import urlparse
            domain = urlparse(lead.website).hostname or lead.website
            domain = domain.replace("www.", "")
            
            guess_patterns = [
                f"info@{domain}",
                f"contact@{domain}",
                f"hello@{domain}",
                f"sales@{domain}",
                f"support@{domain}",
            ]
            
            for pattern in guess_patterns:
                discovered_emails.append({
                    "email": pattern,
                    "source": "pattern_guess",
                    "confidence": "low"
                })
        
        # Validate and save discovered emails
        if discovered_emails:
            from app.services.email_verifier import EmailVerifierService
            
            for email_data in discovered_emails[:3]:  # Limit to top 3
                email = email_data["email"]
                
                # Basic validation
                try:
                    validation = EmailVerifierService.verify_email(email)
                    
                    if validation.get("is_valid"):
                        contact = LeadContact(
                            lead_id=uuid.UUID(str(lead_id)),
                            contact_type=ContactType.EMAIL,
                            original_value=email,
                            normalized_value=email.lower().strip(),
                            verification_status="unverified",
                            source_url=email_data["source"]
                        )
                        db.add(contact)
                        lead.email_enrichment_status = 'completed'
                        db.commit()
                        
                        return {
                            "success": True,
                            "email": email,
                            "source": email_data["source"],
                            "confidence": email_data["confidence"]
                        }
                except Exception as e:
                    logger.warning(f"Email validation failed for {email}: {e}")
                    continue
        
        # No email found
        lead.email_enrichment_status = 'failed'
        db.commit()
        
        # Log exception
        from app.models.automation import LeadException
        exception = LeadException(
            lead_id=uuid.UUID(str(lead_id)),
            exception_type="EMAIL_ENRICHMENT_FAILED",
            reason=f"Could not find valid email for {lead.business_name}",
            severity="warning"
        )
        db.add(exception)
        db.commit()
        
        return {"success": False, "error": "No valid email found"}
    
    @classmethod
    async def bulk_enrich_emails(cls, lead_ids: List[str], db: Session) -> Dict[str, Any]:
        """Enrich emails for multiple leads."""
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        for lead_id in lead_ids:
            result = await cls.enrich_lead_email(lead_id, db)
            if result.get("success"):
                results["success"] += 1
            elif result.get("error") == "Lead not found":
                results["skipped"] += 1
            else:
                results["failed"] += 1
        
        return results
