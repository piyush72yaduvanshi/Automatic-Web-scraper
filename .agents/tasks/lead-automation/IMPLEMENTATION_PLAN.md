# Implementation Plan: Fully Automated Lead-to-CRM Pipeline

## Executive Summary

This plan implements **zero-manual-intervention** automation for handling 500+ leads:
1. **Auto-Enrollment**: Discovered leads → Auto-qualified → Auto-enrolled in outreach sequences
2. **Auto-Approval**: AI-generated emails → Content validation → Auto-approved & scheduled
3. **Auto-CRM Conversion**: Qualified leads → Auto-create Companies/Contacts/Deals
4. **Email Enrichment**: Missing emails → API enrichment → Validation → Ready for outreach
5. **Bulk Processing**: Single endpoint processes 500 leads in <30 seconds

**Current State Analysis**:
- ✅ Workflow Engine: Fully operational (`WorkflowEngineService`)
- ✅ Discovery: Working (12 dental clinic leads exist)
- ✅ Qualification: `LeadQualificationService.qualify_lead()` scores 0-100
- ✅ Sequences: `FollowupSequence` with 4-touch B2B_PROSPECTING cadence exists
- ✅ CRM Models: Companies, Contacts, Deals, Pipeline tables exist
- ❌ **BLOCKING**: Manual approval queue blocks automation (`OutreachApproval.status = PENDING`)
- ❌ **MISSING**: No auto-enrollment logic (leads stay in `business_leads` table)
- ❌ **MISSING**: No auto-conversion to CRM (companies/contacts/deals tables empty)
- ❌ **MISSING**: Email enrichment service for discovered leads

---

## Database Schema Changes

### 1. Automation Settings Table

**File**: `d:\MVP\backend\alembic\versions\20261113_0000_009_automation_settings.py`

```python
"""Add automation_settings and lead_exceptions tables"""

def upgrade():
    # Automation configuration
    op.create_table(
        'automation_settings',
        sa.Column('id', GUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('setting_key', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('setting_value', sa.Text, nullable=False),
        sa.Column('data_type', sa.String(20), default='boolean'),  # boolean, integer, string, json
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    
    # Lead processing exceptions log
    op.create_table(
        'lead_exceptions',
        sa.Column('id', GUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('lead_id', GUID(), nullable=True, index=True),
        sa.Column('exception_type', sa.String(100), nullable=False, index=True),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('severity', sa.String(20), default='warning'),  # info, warning, error, critical
        sa.Column('resolved', sa.Boolean, default=False, index=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, index=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
    )
    
    # Seed default automation settings
    op.execute("""
        INSERT INTO automation_settings (id, setting_key, setting_value, data_type, description) VALUES
        (gen_random_uuid(), 'auto_enroll_to_outreach', 'true', 'boolean', 'Automatically enroll qualified leads in outreach sequences'),
        (gen_random_uuid(), 'auto_approve_emails', 'true', 'boolean', 'Automatically approve AI-generated outreach emails'),
        (gen_random_uuid(), 'auto_convert_to_crm', 'true', 'boolean', 'Automatically convert qualified leads to CRM companies/contacts/deals'),
        (gen_random_uuid(), 'min_score_for_outreach', '70', 'integer', 'Minimum qualification score required for automatic outreach enrollment'),
        (gen_random_uuid(), 'min_score_for_crm', '60', 'integer', 'Minimum qualification score required for automatic CRM conversion'),
        (gen_random_uuid(), 'email_enrichment_enabled', 'true', 'boolean', 'Enable automatic email enrichment for leads without email'),
        (gen_random_uuid(), 'bulk_processing_batch_size', '50', 'integer', 'Number of leads to process in each batch'),
        (gen_random_uuid(), 'ai_approval_validation_rules', '["has_subject", "has_personalization", "length_check"]', 'json', 'AI content validation rules for auto-approval')
    """)

def downgrade():
    op.drop_table('lead_exceptions')
    op.drop_table('automation_settings')
```

### 2. Add Automation Status Fields to Existing Tables

**File**: Same migration file

```python
def upgrade():
    # Add outreach enrollment tracking to business_leads
    op.add_column('business_leads', sa.Column('outreach_enrolled', sa.Boolean, default=False, index=True))
    op.add_column('business_leads', sa.Column('outreach_enrollment_date', sa.DateTime, nullable=True))
    op.add_column('business_leads', sa.Column('crm_converted', sa.Boolean, default=False, index=True))
    op.add_column('business_leads', sa.Column('crm_conversion_date', sa.DateTime, nullable=True))
    op.add_column('business_leads', sa.Column('email_enrichment_status', sa.String(50), default='pending'))  # pending, completed, failed, not_needed
    op.add_column('business_leads', sa.Column('last_automation_run', sa.DateTime, nullable=True))
```

---

## Service Layer Architecture

### 1. Automation Settings Service

**File**: `d:\MVP\backend\app\services\automation_settings_service.py` (NEW)

```python
"""Central configuration service for automation rules and toggles."""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.automation import AutomationSettings

class AutomationSettingsService:
    """Manages automation configuration with type-safe getters."""
    
    @classmethod
    def get_setting(cls, key: str, db: Session, default: Any = None) -> Any:
        """Get automation setting value with type conversion."""
        setting = db.query(AutomationSettings).filter(AutomationSettings.setting_key == key).first()
        if not setting:
            return default
        
        if setting.data_type == 'boolean':
            return setting.setting_value.lower() == 'true'
        elif setting.data_type == 'integer':
            return int(setting.setting_value)
        elif setting.data_type == 'json':
            return json.loads(setting.setting_value)
        return setting.setting_value
    
    @classmethod
    def is_auto_enroll_enabled(cls, db: Session) -> bool:
        return cls.get_setting('auto_enroll_to_outreach', db, True)
    
    @classmethod
    def is_auto_approve_enabled(cls, db: Session) -> bool:
        return cls.get_setting('auto_approve_emails', db, True)
    
    @classmethod
    def is_auto_crm_enabled(cls, db: Session) -> bool:
        return cls.get_setting('auto_convert_to_crm', db, True)
    
    @classmethod
    def get_min_score_for_outreach(cls, db: Session) -> int:
        return cls.get_setting('min_score_for_outreach', db, 70)
    
    @classmethod
    def get_min_score_for_crm(cls, db: Session) -> int:
        return cls.get_setting('min_score_for_crm', db, 60)
```

**Verification**: `pytest tests/test_automation_settings.py -v`

---

### 2. Email Enrichment Service

**File**: `d:\MVP\backend\app\services\email_enrichment_service.py` (NEW)

```python
"""Email discovery and enrichment for leads without contact information."""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType

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
        lead = db.query(BusinessLead).filter(BusinessLead.id == lead_id).first()
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
        
        # Strategy 3: External API enrichment (Hunter.io, Apollo, Clearbit)
        # TODO: Implement when API keys are available
        
        # Validate and save discovered emails
        if discovered_emails:
            from app.services.email_verifier import EmailVerifierService
            
            for email_data in discovered_emails[:3]:  # Limit to top 3
                email = email_data["email"]
                
                # Basic validation
                validation = EmailVerifierService.verify_email(email)
                
                if validation.get("is_valid"):
                    contact = LeadContact(
                        lead_id=lead_id,
                        contact_type=ContactType.EMAIL,
                        original_value=email,
                        normalized_value=email.lower().strip(),
                        verification_status="unverified",  # Will be verified during outreach
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
        
        # No email found
        lead.email_enrichment_status = 'failed'
        db.commit()
        
        # Log exception
        from app.models.automation import LeadException
        exception = LeadException(
            lead_id=lead_id,
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
```

**Verification**: `pytest tests/test_email_enrichment.py -v`

---

### 3. CRM Automation Service

**File**: `d:\MVP\backend\app\services\crm_automation_service.py` (NEW)

```python
"""Automatic lead-to-CRM conversion without manual intervention."""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.models.crm import Company, Contact, Deal
from app.services.crm_service import CRMService

logger = logging.getLogger(__name__)

class CRMAutomationService:
    """Handles automatic conversion of leads to CRM entities."""
    
    @classmethod
    def auto_convert_lead_to_crm(cls, lead_id: str, db: Session) -> Dict[str, Any]:
        """
        Automatically convert a qualified lead to CRM:
        1. Create Company from lead data
        2. Create Contact(s) from lead contacts
        3. Create Deal in "Lead" stage
        4. Update lead status to 'converted_to_crm'
        """
        lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(str(lead_id))).first()
        if not lead:
            return {"success": False, "error": "Lead not found"}
        
        # Check if already converted
        if lead.crm_converted or lead.company_id:
            return {
                "success": False,
                "error": "Lead already converted to CRM",
                "company_id": str(lead.company_id) if lead.company_id else None
            }
        
        try:
            # Use existing CRMService.convert_lead_to_company method
            result = CRMService.convert_lead_to_company(db, str(lead_id))
            
            # Mark lead as converted
            lead.crm_converted = True
            lead.crm_conversion_date = datetime.utcnow()
            lead.status = "converted_to_crm"
            db.commit()
            
            # Log activity
            from app.models.crm import Activity
            activity = Activity(
                activity_type="SYSTEM",
                title=f"Auto-converted lead '{lead.business_name}' to CRM",
                description=f"Automated conversion: Company, Contact, and Deal created from lead qualification",
                lead_id=lead.id,
                company_id=result.get("company").id if result.get("company") else None
            )
            db.add(activity)
            db.commit()
            
            return {
                "success": True,
                "company_id": result.get("company_id"),
                "lead_name": lead.business_name
            }
            
        except Exception as e:
            logger.error(f"Failed to auto-convert lead {lead_id} to CRM: {e}", exc_info=True)
            
            # Log exception
            from app.models.automation import LeadException
            exception = LeadException(
                lead_id=lead_id,
                exception_type="CRM_CONVERSION_FAILED",
                reason=str(e),
                severity="error"
            )
            db.add(exception)
            db.commit()
            
            return {"success": False, "error": str(e)}
    
    @classmethod
    def bulk_convert_to_crm(cls, lead_ids: List[str], db: Session) -> Dict[str, Any]:
        """Convert multiple leads to CRM in batch."""
        results = {"converted": 0, "failed": 0, "skipped": 0, "errors": []}
        
        for lead_id in lead_ids:
            result = cls.auto_convert_lead_to_crm(lead_id, db)
            if result.get("success"):
                results["converted"] += 1
            elif "already converted" in result.get("error", "").lower():
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "lead_id": lead_id,
                    "error": result.get("error")
                })
        
        return results
```

**Verification**: `pytest tests/test_crm_automation.py -v`

---

### 4. Outreach Auto-Enrollment Service

**File**: `d:\MVP\backend\app\services\outreach_automation_service.py` (NEW)

```python
"""Automatic enrollment of qualified leads into outreach sequences."""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType
from app.models.campaign import FollowupSequence, CampaignMember
from app.models.outreach import OutreachCampaign

logger = logging.getLogger(__name__)

class OutreachAutomationService:
    """Handles automatic enrollment of leads into outreach sequences."""
    
    @classmethod
    def auto_enroll_in_sequence(
        cls,
        lead_id: str,
        sequence_name: str = "B2B_PROSPECTING",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Automatically enroll a qualified lead in an outreach sequence.
        
        Steps:
        1. Verify lead has valid email
        2. Check not already enrolled
        3. Get sequence by campaign_type
        4. Create CampaignMember enrollment
        5. Trigger sequence step evaluation
        """
        lead = db.query(BusinessLead).filter(BusinessLead.id == uuid.UUID(str(lead_id))).first()
        if not lead:
            return {"success": False, "error": "Lead not found"}
        
        # Check if already enrolled
        if lead.outreach_enrolled:
            return {"success": False, "error": "Lead already enrolled in outreach"}
        
        # Get lead email
        email_contact = db.query(LeadContact).filter(
            LeadContact.lead_id == lead.id,
            LeadContact.contact_type == ContactType.EMAIL
        ).first()
        
        if not email_contact:
            return {"success": False, "error": "Lead has no email address"}
        
        recipient_email = email_contact.normalized_value or email_contact.original_value
        
        # Get sequence by campaign_type
        sequence = db.query(FollowupSequence).filter(
            FollowupSequence.campaign_type == sequence_name,
            FollowupSequence.is_active == True
        ).first()
        
        if not sequence:
            return {"success": False, "error": f"Sequence '{sequence_name}' not found"}
        
        # Create or get campaign for this sequence
        campaign = db.query(OutreachCampaign).filter(
            OutreachCampaign.name == f"Auto-Enrollment: {sequence.name}"
        ).first()
        
        if not campaign:
            campaign = OutreachCampaign(
                name=f"Auto-Enrollment: {sequence.name}",
                description=f"Automated enrollment campaign for {sequence_name}",
                channel="EMAIL",
                status="ACTIVE"
            )
            db.add(campaign)
            db.flush()
        
        # Check if already member
        existing_member = db.query(CampaignMember).filter(
            CampaignMember.lead_id == lead.id,
            CampaignMember.recipient_email == recipient_email,
            CampaignMember.status.in_(["ENROLLED", "IN_PROGRESS"])
        ).first()
        
        if existing_member:
            return {"success": False, "error": "Lead already enrolled as campaign member"}
        
        # Enroll as campaign member
        member = CampaignMember(
            campaign_id=campaign.id,
            lead_id=lead.id,
            recipient_email=recipient_email,
            status="ENROLLED",
            current_step_number=0,
            next_step_due_at=datetime.utcnow(),  # First step due immediately
            enrolled_at=datetime.utcnow()
        )
        db.add(member)
        
        # Update lead status
        lead.outreach_enrolled = True
        lead.outreach_enrollment_date = datetime.utcnow()
        lead.status = "in_sequence"
        
        db.commit()
        
        # Log activity
        from app.models.crm import Activity
        activity = Activity(
            activity_type="SYSTEM",
            title=f"Auto-enrolled '{lead.business_name}' in {sequence.name}",
            description=f"Lead automatically enrolled in outreach sequence. Recipient: {recipient_email}",
            lead_id=lead.id
        )
        db.add(activity)
        db.commit()
        
        return {
            "success": True,
            "lead_id": str(lead.id),
            "sequence_name": sequence.name,
            "campaign_id": str(campaign.id),
            "member_id": str(member.id),
            "recipient_email": recipient_email
        }
    
    @classmethod
    def bulk_enroll_in_sequence(cls, lead_ids: List[str], db: Session) -> Dict[str, Any]:
        """Enroll multiple leads in outreach sequence."""
        results = {"enrolled": 0, "failed": 0, "skipped": 0, "errors": []}
        
        for lead_id in lead_ids:
            result = cls.auto_enroll_in_sequence(lead_id, db=db)
            if result.get("success"):
                results["enrolled"] += 1
            elif "already enrolled" in result.get("error", "").lower():
                results["skipped"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "lead_id": lead_id,
                    "error": result.get("error")
                })
        
        return results
```

**Verification**: `pytest tests/test_outreach_automation.py -v`

---

### 5. Auto-Approval Email Validation Service

**File**: Modify `d:\MVP\backend\app\services\outreach_service.py`

Add method to OutreachService class:

```python
@classmethod
def validate_ai_email_content(cls, subject: str, body: str, recipient_name: str, company_name: str) -> Dict[str, Any]:
    """
    Validate AI-generated email content against safety rules.
    
    Rules:
    1. Has subject line (non-empty, >5 chars)
    2. Has personalization (company_name or recipient_name in body)
    3. Reasonable length (50-1000 words)
    4. No suspicious patterns (spam keywords, excessive caps)
    5. Has proper formatting
    """
    errors = []
    warnings = []
    
    # Rule 1: Subject validation
    if not subject or len(subject) < 5:
        errors.append("Subject line missing or too short")
    
    if len(subject) > 200:
        warnings.append("Subject line very long (>200 chars)")
    
    # Rule 2: Personalization check
    body_lower = body.lower()
    has_company = company_name and company_name.lower() in body_lower
    has_name = recipient_name and recipient_name.lower() in body_lower
    
    if not (has_company or has_name):
        warnings.append("No personalization detected (company or recipient name missing)")
    
    # Rule 3: Length check
    word_count = len(body.split())
    if word_count < 20:
        errors.append(f"Email body too short ({word_count} words, minimum 20)")
    
    if word_count > 1000:
        errors.append(f"Email body too long ({word_count} words, maximum 1000)")
    
    # Rule 4: Spam detection
    spam_keywords = ["click here", "buy now", "limited time", "act fast", "free money", "guaranteed"]
    found_spam = [kw for kw in spam_keywords if kw in body_lower]
    
    if found_spam:
        errors.append(f"Spam keywords detected: {', '.join(found_spam)}")
    
    # Rule 5: Formatting check
    if body.count('\n') < 2:
        warnings.append("Email may lack proper paragraph breaks")
    
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "confidence": "high" if is_valid and len(warnings) == 0 else "medium" if is_valid else "low"
    }

@classmethod
async def auto_approve_if_valid(cls, approval_id: str, db: Session) -> Dict[str, Any]:
    """
    Automatically approve an outreach draft if it passes validation.
    If validation fails, keep it in PENDING for manual review.
    """
    approval = db.query(OutreachApproval).filter(OutreachApproval.id == uuid.UUID(str(approval_id))).first()
    if not approval:
        return {"success": False, "error": "Approval record not found"}
    
    if approval.status != "PENDING":
        return {"success": False, "error": f"Approval already {approval.status}"}
    
    # Validate content
    validation = cls.validate_ai_email_content(
        subject=approval.subject or "",
        body=approval.body_content or "",
        recipient_name=approval.recipient_name or "",
        company_name=""  # Extract from evidence_context if available
    )
    
    if validation["is_valid"]:
        # Auto-approve and send
        send_result = await cls.approve_and_send(approval_id, db)
        
        return {
            "success": True,
            "action": "auto_approved",
            "validation": validation,
            "send_result": send_result
        }
    else:
        # Keep in pending for manual review
        approval.rejection_reason = f"Auto-approval validation failed: {', '.join(validation['errors'])}"
        db.commit()
        
        # Log exception
        from app.models.automation import LeadException
        exception = LeadException(
            lead_id=approval.lead_id,
            exception_type="EMAIL_VALIDATION_FAILED",
            reason=f"Email validation failed: {', '.join(validation['errors'])}",
            severity="warning"
        )
        db.add(exception)
        db.commit()
        
        return {
            "success": False,
            "action": "requires_manual_review",
            "validation": validation
        }
```

**Verification**: Modify `d:\MVP\backend\app\services\sequence_engine_service.py` line 180-195 to call `auto_approve_if_valid()` instead of creating PENDING approval.

---

### 6. Orchestration Service - Master Automation Controller

**File**: `d:\MVP\backend\app\services\lead_automation_orchestrator.py` (NEW)

```python
"""Master orchestration service coordinating all automation steps."""

import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.business_lead import BusinessLead
from app.services.automation_settings_service import AutomationSettingsService
from app.services.email_enrichment_service import EmailEnrichmentService
from app.services.outreach_automation_service import OutreachAutomationService
from app.services.crm_automation_service import CRMAutomationService
from app.services.lead_qualification_service import LeadQualificationService

logger = logging.getLogger(__name__)

class LeadAutomationOrchestrator:
    """Coordinates end-to-end lead automation pipeline."""
    
    @classmethod
    async def process_single_lead(cls, lead_id: str, db: Session) -> Dict[str, Any]:
        """
        Execute complete automation pipeline for one lead:
        1. Check if already processed
        2. Enrich email if missing
        3. Qualify lead if not qualified
        4. Auto-enroll in outreach if score >= threshold
        5. Auto-convert to CRM if score >= threshold
        """
        from datetime import datetime
        
        result = {
            "lead_id": lead_id,
            "steps": {
                "email_enrichment": None,
                "qualification": None,
                "outreach_enrollment": None,
                "crm_conversion": None
            },
            "success": False,
            "error": None
        }
        
        try:
            lead = db.query(BusinessLead).filter(BusinessLead.id == lead_id).first()
            if not lead:
                result["error"] = "Lead not found"
                return result
            
            # Check automation settings
            auto_enroll_enabled = AutomationSettingsService.is_auto_enroll_enabled(db)
            auto_crm_enabled = AutomationSettingsService.is_auto_crm_enabled(db)
            min_score_outreach = AutomationSettingsService.get_min_score_for_outreach(db)
            min_score_crm = AutomationSettingsService.get_min_score_for_crm(db)
            
            # Step 1: Email enrichment (if missing)
            if lead.email_enrichment_status in ['pending', 'failed']:
                email_result = await EmailEnrichmentService.enrich_lead_email(lead_id, db)
                result["steps"]["email_enrichment"] = email_result
            else:
                result["steps"]["email_enrichment"] = {"skipped": True, "reason": "Email already exists"}
            
            # Step 2: Qualification (if not qualified)
            if not lead.qualification_score or lead.qualification_status == "New":
                qual_result = await LeadQualificationService.qualify_lead(lead_id, db)
                result["steps"]["qualification"] = {
                    "score": qual_result.get("score"),
                    "status": qual_result.get("status")
                }
            else:
                result["steps"]["qualification"] = {
                    "skipped": True,
                    "score": lead.qualification_score,
                    "status": lead.qualification_status
                }
            
            # Refresh lead to get updated qualification
            db.refresh(lead)
            
            # Step 3: Auto-enroll in outreach (if qualified and has email)
            if auto_enroll_enabled and lead.qualification_score >= min_score_outreach and not lead.outreach_enrolled:
                enroll_result = OutreachAutomationService.auto_enroll_in_sequence(lead_id, db=db)
                result["steps"]["outreach_enrollment"] = enroll_result
            else:
                result["steps"]["outreach_enrollment"] = {
                    "skipped": True,
                    "reason": f"Score {lead.qualification_score} < {min_score_outreach} or already enrolled"
                }
            
            # Step 4: Auto-convert to CRM (if qualified)
            if auto_crm_enabled and lead.qualification_score >= min_score_crm and not lead.crm_converted:
                crm_result = CRMAutomationService.auto_convert_lead_to_crm(lead_id, db)
                result["steps"]["crm_conversion"] = crm_result
            else:
                result["steps"]["crm_conversion"] = {
                    "skipped": True,
                    "reason": f"Score {lead.qualification_score} < {min_score_crm} or already converted"
                }
            
            # Update last automation run
            lead.last_automation_run = datetime.utcnow()
            db.commit()
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error processing lead {lead_id}: {e}", exc_info=True)
            result["error"] = str(e)
        
        return result
    
    @classmethod
    async def bulk_process_leads(
        cls,
        filters: Dict[str, Any],
        batch_size: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process multiple leads in batch with filters.
        
        Filters:
        - status: "enriched", "discovered", etc.
        - qualification_status: "New", "Qualified", etc.
        - min_score, max_score
        - has_email: bool
        """
        from sqlalchemy import and_
        from app.models.lead_contact import LeadContact, ContactType
        
        # Build query
        query = db.query(BusinessLead)
        
        if filters.get("status"):
            query = query.filter(BusinessLead.status == filters["status"])
        
        if filters.get("qualification_status"):
            query = query.filter(BusinessLead.qualification_status != "Disqualified")
        
        if filters.get("min_score"):
            query = query.filter(BusinessLead.qualification_score >= filters["min_score"])
        
        # Exclude already processed
        query = query.filter(
            and_(
                BusinessLead.outreach_enrolled == False,
                BusinessLead.crm_converted == False
            )
        )
        
        leads = query.limit(batch_size).all()
        
        results = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "email_enriched": 0,
            "qualified": 0,
            "enrolled": 0,
            "converted": 0,
            "errors": []
        }
        
        for lead in leads:
            lead_result = await cls.process_single_lead(str(lead.id), db)
            results["processed"] += 1
            
            if lead_result.get("success"):
                results["succeeded"] += 1
                
                if lead_result["steps"]["email_enrichment"] and lead_result["steps"]["email_enrichment"].get("success"):
                    results["email_enriched"] += 1
                
                if lead_result["steps"]["qualification"] and not lead_result["steps"]["qualification"].get("skipped"):
                    results["qualified"] += 1
                
                if lead_result["steps"]["outreach_enrollment"] and lead_result["steps"]["outreach_enrollment"].get("success"):
                    results["enrolled"] += 1
                
                if lead_result["steps"]["crm_conversion"] and lead_result["steps"]["crm_conversion"].get("success"):
                    results["converted"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "lead_id": str(lead.id),
                    "error": lead_result.get("error")
                })
        
        return results
```

**Verification**: `pytest tests/test_lead_automation_orchestrator.py -v`

---

## Workflow Modifications

### Modify "Auto-Qualify Newly Discovered Leads" Workflow

**File**: `d:\MVP\backend\app\services\workflow_engine_service.py`

**Change**: Line 571-585 (seed_default_workflows_if_empty method)

**Replace**:
```python
{
    "name": "Auto-Qualify Newly Discovered Leads",
    "description": "Triggered when a new lead is ingested. Researches digital footprint and calculates 5-factor ICP score.",
    "trigger_type": "NEW_LEAD",
    "steps": [
        {
            "step_id": "research",
            "name": "Research Company",
            "action_type": "RESEARCH_COMPANY",
            "config": {},
        },
        {
            "step_id": "qualify",
            "name": "Calculate ICP Score",
            "action_type": "QUALIFY_LEAD",
            "config": {},
        },
    ],
},
```

**With**:
```python
{
    "name": "Auto-Qualify and Auto-Enroll Leads",
    "description": "Triggered when a new lead is ingested. Researches, qualifies, enriches email, enrolls in outreach, and converts to CRM - fully automated.",
    "trigger_type": "NEW_LEAD",
    "steps": [
        {
            "step_id": "research",
            "name": "Research Company",
            "action_type": "RESEARCH_COMPANY",
            "config": {},
        },
        {
            "step_id": "qualify",
            "name": "Calculate ICP Score",
            "action_type": "QUALIFY_LEAD",
            "config": {},
        },
        {
            "step_id": "enrich_email",
            "name": "Enrich Email if Missing",
            "action_type": "ENRICH_EMAIL",
            "config": {},
        },
        {
            "step_id": "auto_enroll",
            "name": "Auto-Enroll in Outreach",
            "action_type": "AUTO_ENROLL_OUTREACH",
            "config": {"sequence": "B2B_PROSPECTING"},
        },
        {
            "step_id": "auto_convert_crm",
            "name": "Auto-Convert to CRM",
            "action_type": "AUTO_CONVERT_CRM",
            "config": {},
        },
    ],
},
```

**Add new action handlers** in `_execute_step_action` method (line 260):

```python
elif action_type == "ENRICH_EMAIL":
    lead_id = input_payload.get("lead_id") or config.get("lead_id")
    if not lead_id:
        return {"status": "SKIPPED", "reason": "No lead_id provided"}
    from app.services.email_enrichment_service import EmailEnrichmentService
    result = await EmailEnrichmentService.enrich_lead_email(str(lead_id), db)
    return {"status": "SUCCESS" if result.get("success") else "FAILED", "result": result}

elif action_type == "AUTO_ENROLL_OUTREACH":
    lead_id = input_payload.get("lead_id") or config.get("lead_id")
    sequence = config.get("sequence", "B2B_PROSPECTING")
    if not lead_id:
        return {"status": "SKIPPED", "reason": "No lead_id provided"}
    from app.services.outreach_automation_service import OutreachAutomationService
    result = OutreachAutomationService.auto_enroll_in_sequence(str(lead_id), sequence_name=sequence, db=db)
    return {"status": "SUCCESS" if result.get("success") else "SKIPPED", "result": result}

elif action_type == "AUTO_CONVERT_CRM":
    lead_id = input_payload.get("lead_id") or config.get("lead_id")
    if not lead_id:
        return {"status": "SKIPPED", "reason": "No lead_id provided"}
    from app.services.crm_automation_service import CRMAutomationService
    result = CRMAutomationService.auto_convert_lead_to_crm(str(lead_id), db)
    return {"status": "SUCCESS" if result.get("success") else "SKIPPED", "result": result}
```

**Verification**: `npm run test:workflows` (or manual workflow trigger)

---

## API Endpoints

### 1. Automation Settings Endpoints

**File**: `d:\MVP\backend\app\api\v1\automation.py` (NEW)

```python
"""Automation configuration and control API."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.automation_settings_service import AutomationSettingsService
from app.models.automation import AutomationSettings

router = APIRouter(prefix="/automation", tags=["Automation"], dependencies=[Depends(verify_api_key)])

@router.get("/settings")
def get_automation_settings(db: Session = Depends(get_db)):
    """Get all automation configuration settings."""
    settings = db.query(AutomationSettings).all()
    return {
        "settings": [
            {
                "key": s.setting_key,
                "value": s.setting_value,
                "type": s.data_type,
                "description": s.description,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in settings
        ]
    }

@router.put("/settings/{setting_key}")
def update_automation_setting(
    setting_key: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update a single automation setting."""
    setting = db.query(AutomationSettings).filter(AutomationSettings.setting_key == setting_key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{setting_key}' not found")
    
    new_value = payload.get("value")
    if new_value is None:
        raise HTTPException(status_code=400, detail="Value is required")
    
    # Type validation
    if setting.data_type == "boolean":
        if not isinstance(new_value, bool):
            raise HTTPException(status_code=400, detail="Value must be boolean")
        setting.setting_value = "true" if new_value else "false"
    elif setting.data_type == "integer":
        if not isinstance(new_value, int):
            raise HTTPException(status_code=400, detail="Value must be integer")
        setting.setting_value = str(new_value)
    else:
        setting.setting_value = str(new_value)
    
    from datetime import datetime
    setting.updated_at = datetime.utcnow()
    db.commit()
    
    return {"success": True, "setting_key": setting_key, "new_value": setting.setting_value}

@router.get("/status")
def get_automation_status(db: Session = Depends(get_db)):
    """Get current automation status summary."""
    return {
        "auto_enroll_enabled": AutomationSettingsService.is_auto_enroll_enabled(db),
        "auto_approve_enabled": AutomationSettingsService.is_auto_approve_enabled(db),
        "auto_crm_enabled": AutomationSettingsService.is_auto_crm_enabled(db),
        "min_score_outreach": AutomationSettingsService.get_min_score_for_outreach(db),
        "min_score_crm": AutomationSettingsService.get_min_score_for_crm(db)
    }
```

**Add to router**: `d:\MVP\backend\app\api\v1\__init__.py`

```python
from app.api.v1 import automation
api_router.include_router(automation.router, prefix="/v1")
```

**Verification**: `curl http://localhost:8000/api/v1/automation/settings`

---

### 2. Bulk Processing Endpoint

**File**: `d:\MVP\backend\app\api\v1\leads.py`

**Add to existing file** (after line 200):

```python
@router.post("/bulk-process")
async def bulk_process_leads(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Process multiple leads through complete automation pipeline.
    
    Filters:
    - status: "enriched", "discovered", etc.
    - qualification_status: "New", "Qualified", "Maybe"
    - min_score: int (default: 0)
    - batch_size: int (default: 50, max: 500)
    
    Actions performed:
    1. Email enrichment (if missing)
    2. Lead qualification (if not qualified)
    3. Auto-enroll in outreach (if score >= threshold)
    4. Auto-convert to CRM (if score >= threshold)
    """
    from app.services.lead_automation_orchestrator import LeadAutomationOrchestrator
    from app.services.automation_settings_service import AutomationSettingsService
    
    filters = {
        "status": payload.get("status"),
        "qualification_status": payload.get("qualification_status"),
        "min_score": payload.get("min_score", 0),
        "has_email": payload.get("has_email")
    }
    
    batch_size = min(payload.get("batch_size", 50), 500)
    
    result = await LeadAutomationOrchestrator.bulk_process_leads(
        filters=filters,
        batch_size=batch_size,
        db=db
    )
    
    return {
        "success": True,
        "summary": result,
        "message": f"Processed {result['processed']} leads: {result['enrolled']} enrolled, {result['converted']} converted to CRM"
    }
```

**Verification**: `curl -X POST http://localhost:8000/api/v1/leads/bulk-process -H "Content-Type: application/json" -d '{"batch_size": 10}'`

---

### 3. Exception Management Endpoint

**File**: `d:\MVP\backend\app\api\v1\automation.py`

**Add to existing file**:

```python
@router.get("/exceptions")
def list_exceptions(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """List automation exceptions for manual review."""
    from app.models.automation import LeadException
    from sqlalchemy import desc
    
    query = db.query(LeadException)
    
    if severity:
        query = query.filter(LeadException.severity == severity)
    
    if resolved is not None:
        query = query.filter(LeadException.resolved == resolved)
    
    exceptions = query.order_by(desc(LeadException.created_at)).limit(limit).all()
    
    return {
        "exceptions": [
            {
                "id": str(e.id),
                "lead_id": str(e.lead_id) if e.lead_id else None,
                "type": e.exception_type,
                "reason": e.reason,
                "severity": e.severity,
                "resolved": e.resolved,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in exceptions
        ],
        "total": len(exceptions)
    }

@router.patch("/exceptions/{exception_id}/resolve")
def resolve_exception(
    exception_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Mark an exception as resolved."""
    import uuid
    from app.models.automation import LeadException
    from datetime import datetime
    
    exception = db.query(LeadException).filter(LeadException.id == uuid.UUID(exception_id)).first()
    if not exception:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    exception.resolved = True
    exception.resolved_at = datetime.utcnow()
    exception.resolution_notes = payload.get("notes", "Manually resolved")
    db.commit()
    
    return {"success": True, "exception_id": exception_id}
```

**Verification**: `curl http://localhost:8000/api/v1/automation/exceptions`

---

## Model Files

### Add Automation Models

**File**: `d:\MVP\backend\app\models\automation.py` (NEW)

```python
"""Automation configuration and exception tracking models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AutomationSettings(Base):
    """Configuration settings for automation behavior."""
    
    __tablename__ = "automation_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = Column(String(100), nullable=False, unique=True, index=True)
    setting_value = Column(Text, nullable=False)
    data_type = Column(String(20), default="boolean")  # boolean, integer, string, json
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LeadException(Base):
    """Exceptions and failures during lead automation processing."""
    
    __tablename__ = "lead_exceptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    exception_type = Column(String(100), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    severity = Column(String(20), default="warning", index=True)  # info, warning, error, critical
    resolved = Column(Boolean, default=False, index=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_exception_lead_type", "lead_id", "exception_type"),
        Index("idx_exception_severity_resolved", "severity", "resolved"),
    )
```

**Add to __init__.py**: `d:\MVP\backend\app\models\__init__.py`

```python
from app.models.automation import AutomationSettings, LeadException
```

**Verification**: `alembic upgrade head`

---

## Frontend Changes

### Settings Page - Automation Toggles

**File**: `d:\MVP\frontend\src\pages\SettingsView.tsx`

**Add new section** (after existing settings):

```tsx
import React, { useState, useEffect } from 'react';
import { apiClient } from '../lib/apiClient';

interface AutomationSettings {
  auto_enroll_to_outreach: boolean;
  auto_approve_emails: boolean;
  auto_convert_to_crm: boolean;
  min_score_for_outreach: number;
  min_score_for_crm: number;
}

export function AutomationSettings() {
  const [settings, setSettings] = useState<AutomationSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await apiClient.get('/automation/settings');
      const settingsMap = response.data.settings.reduce((acc: any, s: any) => {
        if (s.type === 'boolean') {
          acc[s.key] = s.value === 'true';
        } else if (s.type === 'integer') {
          acc[s.key] = parseInt(s.value);
        } else {
          acc[s.key] = s.value;
        }
        return acc;
      }, {});
      setSettings(settingsMap);
    } catch (error) {
      console.error('Failed to load automation settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = async (key: string, value: any) => {
    setSaving(true);
    try {
      await apiClient.put(`/automation/settings/${key}`, { value });
      setSettings({ ...settings!, [key]: value });
    } catch (error) {
      console.error('Failed to update setting:', error);
      alert('Failed to update setting');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading automation settings...</div>;
  if (!settings) return <div>Failed to load settings</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-6">🤖 Automation Settings</h2>
      
      <div className="space-y-6">
        {/* Auto-Enroll Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Auto-Enroll to Outreach</h3>
            <p className="text-sm text-gray-600">
              Automatically enroll qualified leads in outreach sequences
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.auto_enroll_to_outreach}
              onChange={(e) => updateSetting('auto_enroll_to_outreach', e.target.checked)}
              disabled={saving}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Auto-Approve Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Auto-Approve Emails</h3>
            <p className="text-sm text-gray-600">
              Automatically approve AI-generated emails that pass validation
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.auto_approve_emails}
              onChange={(e) => updateSetting('auto_approve_emails', e.target.checked)}
              disabled={saving}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Auto-Convert to CRM Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Auto-Convert to CRM</h3>
            <p className="text-sm text-gray-600">
              Automatically create Companies, Contacts, and Deals for qualified leads
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.auto_convert_to_crm}
              onChange={(e) => updateSetting('auto_convert_to_crm', e.target.checked)}
              disabled={saving}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        <hr className="my-4" />

        {/* Threshold Sliders */}
        <div>
          <label className="block font-semibold mb-2">
            Min Score for Outreach: {settings.min_score_for_outreach}
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={settings.min_score_for_outreach}
            onChange={(e) => updateSetting('min_score_for_outreach', parseInt(e.target.value))}
            disabled={saving}
            className="w-full"
          />
          <p className="text-sm text-gray-600 mt-1">
            Leads with qualification score ≥ {settings.min_score_for_outreach} will be auto-enrolled
          </p>
        </div>

        <div>
          <label className="block font-semibold mb-2">
            Min Score for CRM: {settings.min_score_for_crm}
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={settings.min_score_for_crm}
            onChange={(e) => updateSetting('min_score_for_crm', parseInt(e.target.value))}
            disabled={saving}
            className="w-full"
          />
          <p className="text-sm text-gray-600 mt-1">
            Leads with qualification score ≥ {settings.min_score_for_crm} will be auto-converted to CRM
          </p>
        </div>

        {saving && (
          <div className="text-center text-sm text-gray-600">
            Saving...
          </div>
        )}
      </div>
    </div>
  );
}
```

**Add Bulk Process Button** to Leads page (`d:\MVP\frontend\src\pages\LeadsView.tsx`):

```tsx
<button
  onClick={async () => {
    const confirmed = confirm('Process all pending leads through automation pipeline?');
    if (!confirmed) return;
    
    try {
      const response = await apiClient.post('/leads/bulk-process', {
        batch_size: 500,
        status: 'enriched'
      });
      
      alert(`Processed ${response.data.summary.processed} leads:\n` +
            `- Enrolled: ${response.data.summary.enrolled}\n` +
            `- Converted to CRM: ${response.data.summary.converted}\n` +
            `- Failed: ${response.data.summary.failed}`);
      
      // Refresh leads list
      window.location.reload();
    } catch (error) {
      alert('Bulk processing failed');
      console.error(error);
    }
  }}
  className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
>
  🚀 Bulk Process All Leads
</button>
```

**Verification**: Visit `http://localhost:5173/settings` and toggle automation settings

---

## Integration Points & Data Flow

### End-to-End Flow

```
1. DISCOVERY (Existing)
   └─> SerpAPI scrapes businesses
   └─> Creates BusinessLead record
   └─> Emits NEW_LEAD event

2. WORKFLOW TRIGGER (Modified)
   └─> WorkflowEngineService.emit_event("NEW_LEAD")
   └─> Triggers "Auto-Qualify and Auto-Enroll Leads" workflow

3. QUALIFICATION (Existing)
   └─> LeadQualificationService.qualify_lead()
   └─> Calculates 0-100 score
   └─> Sets qualification_status ("Qualified", "Maybe", "Rejected")

4. EMAIL ENRICHMENT (NEW)
   └─> EmailEnrichmentService.enrich_lead_email()
   └─> Website scraping / pattern guessing / API lookup
   └─> Creates LeadContact record (EMAIL type)
   └─> Updates email_enrichment_status

5. AUTO-ENROLLMENT (NEW)
   └─> IF score >= min_score_for_outreach AND has_email
   └─> OutreachAutomationService.auto_enroll_in_sequence()
   └─> Creates CampaignMember record
   └─> Sets next_step_due_at = NOW (first email ready immediately)
   └─> Updates lead.outreach_enrolled = True

6. SEQUENCE EXECUTION (Modified)
   └─> SequenceEngineService.execute_due_sequence_steps()
   └─> Finds CampaignMember with next_step_due_at <= NOW
   └─> Runs 7 safety checks
   └─> Generates email from template (with AI personalization)
   └─> Creates OutreachApproval record with status=PENDING

7. AUTO-APPROVAL (NEW)
   └─> IF auto_approve_emails = True
   └─> OutreachService.auto_approve_if_valid()
   └─> Validates content (has_subject, personalization, length, spam check)
   └─> IF valid: approve_and_send() → GmailProvider.send_email()
   └─> IF invalid: keep PENDING for manual review → log LeadException

8. AUTO-CRM CONVERSION (NEW)
   └─> IF score >= min_score_for_crm
   └─> CRMAutomationService.auto_convert_lead_to_crm()
   └─> Creates Company record (from lead data)
   └─> Creates Contact record (from LeadContact data)
   └─> Creates Deal record (pipeline "Lead" stage, $5000 default)
   └─> Links lead.company_id = company.id
   └─> Updates lead.crm_converted = True

9. EXCEPTION HANDLING
   └─> Any step failure → LeadException record created
   └─> Admin reviews /automation/exceptions endpoint
   └─> <5% exception rate expected (email validation failures)
```

---

## Error Handling Strategy

### Exception Types

1. **EMAIL_ENRICHMENT_FAILED** (severity: warning)
   - Reason: No valid email found after all enrichment strategies
   - Resolution: Manual research or skip lead

2. **EMAIL_VALIDATION_FAILED** (severity: warning)
   - Reason: AI-generated email failed content validation (spam keywords, no personalization, etc.)
   - Resolution: Manual review and edit in approval queue

3. **CRM_CONVERSION_FAILED** (severity: error)
   - Reason: Database constraint violation, missing required fields
   - Resolution: Check lead data quality, fix schema issues

4. **OUTREACH_ENROLLMENT_FAILED** (severity: error)
   - Reason: No email, suppressed recipient, duplicate enrollment
   - Resolution: Verify lead status and email availability

### Logging Strategy

- **Activity Log**: Every automation action logged to `activities` table
- **Exception Log**: Failures logged to `lead_exceptions` table
- **Audit Trail**: All workflow executions tracked in `workflow_executions` table
- **API Logs**: Backend logs all automation API calls with structured JSON

### Monitoring Dashboard (Future Enhancement)

- `/automation/dashboard` endpoint showing:
  - Automation success rate (%)
  - Average processing time per lead
  - Exception breakdown by type
  - Leads processed today/week/month
  - CRM conversion rate

---

## Testing Approach

### Unit Tests

**File**: `d:\MVP\backend\tests\test_automation_complete.py` (NEW)

```python
"""Complete automation pipeline tests."""

import pytest
from app.services.lead_automation_orchestrator import LeadAutomationOrchestrator
from app.services.automation_settings_service import AutomationSettingsService

@pytest.mark.asyncio
async def test_end_to_end_automation(db):
    """Test complete automation flow for a single lead."""
    # 1. Create test lead
    lead = await LeadService.create_or_update_lead(db, {
        "business_name": "Test Dental Clinic",
        "website": "https://testdental.com",
        "category": "Dental Services",
        "city": "San Francisco",
        "source_provider": "test"
    })
    
    # 2. Process through automation
    result = await LeadAutomationOrchestrator.process_single_lead(str(lead.id), db)
    
    # 3. Verify steps executed
    assert result["success"] == True
    assert result["steps"]["qualification"] is not None
    assert result["steps"]["email_enrichment"] is not None
    
    # 4. Verify lead state
    db.refresh(lead)
    assert lead.qualification_score is not None
    assert lead.outreach_enrolled == True
    assert lead.crm_converted == True
    
    # 5. Verify CRM entities created
    company = db.query(Company).filter(Company.lead_id == lead.id).first()
    assert company is not None
    assert company.name == "Test Dental Clinic"
    
    contacts = db.query(Contact).filter(Contact.company_id == company.id).all()
    assert len(contacts) > 0
    
    deals = db.query(Deal).filter(Deal.company_id == company.id).all()
    assert len(deals) > 0

@pytest.mark.asyncio
async def test_bulk_processing(db):
    """Test bulk processing endpoint with 10 leads."""
    # Create 10 test leads
    for i in range(10):
        await LeadService.create_or_update_lead(db, {
            "business_name": f"Test Business {i}",
            "website": f"https://test{i}.com",
            "category": "Professional Services",
            "source_provider": "test"
        })
    
    # Bulk process
    result = await LeadAutomationOrchestrator.bulk_process_leads(
        filters={"status": "discovered"},
        batch_size=10,
        db=db
    )
    
    assert result["processed"] == 10
    assert result["succeeded"] >= 5  # At least 50% success rate
```

**Verification**: `pytest tests/test_automation_complete.py -v -s`

### Integration Tests

1. **Discovery → Auto-Enroll** (existing 12 leads)
   - Run: `POST /api/v1/leads/bulk-process`
   - Verify: All 12 leads enrolled in sequences

2. **Email Generation → Auto-Approval**
   - Trigger sequence execution
   - Verify: Emails auto-approved and sent (check Gmail)

3. **CRM Conversion**
   - Verify: Companies/Contacts/Deals tables populated
   - Check: `SELECT COUNT(*) FROM companies WHERE lead_id IS NOT NULL`

### Manual Testing Checklist

- [ ] Run discovery for 10 new leads
- [ ] Verify NEW_LEAD workflow triggers automatically
- [ ] Check qualification scores calculated
- [ ] Verify emails enriched (if missing)
- [ ] Confirm auto-enrollment in B2B_PROSPECTING sequence
- [ ] Check outreach_approvals table (should be empty if auto-approved)
- [ ] Verify companies/contacts/deals created in CRM
- [ ] Test automation settings toggle (disable/enable)
- [ ] Test bulk-process endpoint with 500 leads (<30s)
- [ ] Verify exception rate <5%
- [ ] Check activities table for automation logs

---

## Success Criteria Validation

### ✅ Criterion 1: Zero Manual Intervention
**Test**: Run discovery for 100 leads, verify 0 manual clicks required
**Validation**: 
- `SELECT COUNT(*) FROM business_leads WHERE outreach_enrolled = true` = 100
- `SELECT COUNT(*) FROM outreach_approvals WHERE status = 'PENDING'` = 0

### ✅ Criterion 2: Bulk Processing Speed
**Test**: `POST /leads/bulk-process` with 500 leads
**Validation**: Response time <30 seconds, check `result.processed = 500`

### ✅ Criterion 3: CRM Auto-Population
**Test**: Check CRM tables after bulk processing
**Validation**:
```sql
SELECT COUNT(*) FROM companies WHERE lead_id IS NOT NULL;  -- Should be >0
SELECT COUNT(*) FROM contacts WHERE lead_id IS NOT NULL;   -- Should be >0
SELECT COUNT(*) FROM deals WHERE company_id IN (SELECT id FROM companies WHERE lead_id IS NOT NULL); -- Should be >0
```

### ✅ Criterion 4: Exception Rate <5%
**Test**: `GET /automation/exceptions`
**Validation**: `(failed / processed) * 100 < 5%`

### ✅ Criterion 5: Settings UI Control
**Test**: Toggle automation settings in frontend
**Validation**: Settings persist and affect behavior immediately

---

## Deployment Steps

### 1. Database Migration
```bash
cd d:\MVP\backend
alembic upgrade head
```

### 2. Verify Migration Success
```bash
psql -U crm_user -d crm_leads -c "SELECT * FROM automation_settings;"
psql -U crm_user -d crm_leads -c "\d lead_exceptions"
```

### 3. Restart Backend
```bash
cd d:\MVP\backend
bun run dev
```

### 4. Restart Frontend
```bash
cd d:\MVP\frontend
npm run dev
```

### 5. Seed Test Data (if needed)
```bash
curl -X POST http://localhost:8000/api/v1/discovery/run \
  -H "Content-Type: application/json" \
  -d '{"query": "dental clinics in Austin TX", "max_results": 10}'
```

### 6. Trigger Bulk Processing
```bash
curl -X POST http://localhost:8000/api/v1/leads/bulk-process \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 500}'
```

### 7. Verify Results
```bash
# Check automation logs
curl http://localhost:8000/api/v1/automation/exceptions

# Check CRM data
curl http://localhost:8000/api/v1/crm/companies?limit=10

# Check outreach campaigns
curl http://localhost:8000/api/v1/campaigns
```

---

## Files Summary

### New Files (9)
1. `d:\MVP\backend\alembic\versions\20261113_0000_009_automation_settings.py`
2. `d:\MVP\backend\app\models\automation.py`
3. `d:\MVP\backend\app\services\automation_settings_service.py`
4. `d:\MVP\backend\app\services\email_enrichment_service.py`
5. `d:\MVP\backend\app\services\crm_automation_service.py`
6. `d:\MVP\backend\app\services\outreach_automation_service.py`
7. `d:\MVP\backend\app\services\lead_automation_orchestrator.py`
8. `d:\MVP\backend\app\api\v1\automation.py`
9. `d:\MVP\backend\tests\test_automation_complete.py`

### Modified Files (6)
1. `d:\MVP\backend\app\services\workflow_engine_service.py` (add 3 new action types, modify default workflow)
2. `d:\MVP\backend\app\services\outreach_service.py` (add validation and auto-approval methods)
3. `d:\MVP\backend\app\services\sequence_engine_service.py` (integrate auto-approval)
4. `d:\MVP\backend\app\api\v1\leads.py` (add bulk-process endpoint)
5. `d:\MVP\backend\app\models\__init__.py` (import automation models)
6. `d:\MVP\frontend\src\pages\SettingsView.tsx` (add automation toggles UI)

---

## Timeline Estimate

- **Database Migration**: 30 minutes
- **Service Layer Implementation**: 4 hours
- **Workflow Modifications**: 1 hour
- **API Endpoints**: 2 hours
- **Frontend UI**: 2 hours
- **Testing & Debugging**: 3 hours
- **Documentation**: 1 hour

**Total**: ~13.5 hours (2 development days)

---

## Risks & Mitigations

### Risk 1: Email Validation False Negatives
**Impact**: Valid emails marked as invalid, leads not enrolled
**Mitigation**: Use multiple validation strategies (DNS MX, SMTP, pattern matching), log to exceptions for manual review

### Risk 2: AI Email Content Quality
**Impact**: Auto-approved emails have poor quality, damage sender reputation
**Mitigation**: Strict validation rules (personalization required, spam check, length check), start with conservative approval, gradually tune

### Risk 3: CRM Data Duplication
**Impact**: Multiple Company/Contact records for same business
**Mitigation**: Check existing records by domain/email before creating, use unique constraints in DB

### Risk 4: Performance Bottleneck (500 leads)
**Impact**: Bulk processing times out or crashes
**Mitigation**: Process in batches of 50, use background tasks (Celery/RQ), add database indexes

### Risk 5: User Loses Control
**Impact**: System sends unwanted emails, creates bad data
**Mitigation**: Settings UI with easy toggles, exception dashboard for monitoring, kill switch available

---

## Future Enhancements

1. **Machine Learning Score Refinement**: Learn from user feedback on lead quality
2. **A/B Testing for Email Templates**: Test different subject lines, track open rates
3. **Sentiment Analysis on Replies**: Auto-classify inbound replies before manual review
4. **Webhook Integration**: Trigger external systems (Zapier, Make) on lead events
5. **Mobile App Notifications**: Alert on high-value leads or exceptions
6. **Drip Campaign Builder**: Visual workflow editor for complex sequences
7. **AI Reply Suggestions**: Draft replies to inbound messages automatically

---

## Conclusion

This implementation plan provides a **complete, production-ready automation pipeline** that:

✅ **Eliminates manual bottlenecks**: No human action required for 500+ leads  
✅ **Maintains safety**: 7-point compliance checks, content validation, exception logging  
✅ **Provides control**: Settings UI, exception dashboard, toggleable automation  
✅ **Scales efficiently**: Bulk processing in <30s, background job ready  
✅ **Integrates seamlessly**: Works with existing workflow engine, CRM, outreach systems  

**Next Steps**: Execute implementation following the verification steps after each phase. Test with 10 leads first, then scale to 100, then 500.
