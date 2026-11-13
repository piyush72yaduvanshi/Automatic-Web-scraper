"""Leads API endpoints."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io

from app.core.database import get_db
from app.schemas.lead import (
    BusinessLeadResponse,
    LeadDetailResponse,
    LeadListResponse,
)
from app.services import LeadService
from app.services.lead_automation_orchestrator import LeadAutomationOrchestrator

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    has_email: Optional[bool] = None,
    has_phone: Optional[bool] = None,
    has_social: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    List business leads with filtering and pagination.
    """
    skip = (page - 1) * page_size
    
    leads, total = LeadService.list_leads(
        db,
        skip=skip,
        limit=page_size,
        search=search,
        category=category,
        city=city,
        has_email=has_email,
        has_phone=has_phone,
        has_social=has_social,
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": leads,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/export/csv")
def export_leads_csv(
    search: Optional[str] = None,
    category: Optional[str] = None,
    city: Optional[str] = None,
    has_email: Optional[bool] = None,
    has_phone: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Export filtered leads to CSV with complete contacts and social footprints."""
    leads, _ = LeadService.list_leads(
        db,
        skip=0,
        limit=10000,
        search=search,
        category=category,
        city=city,
        has_email=has_email,
        has_phone=has_phone,
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "business_name",
        "category",
        "primary_phone",
        "all_phones",
        "primary_email",
        "all_emails",
        "website",
        "linkedin",
        "instagram",
        "facebook",
        "twitter_x",
        "address",
        "city",
        "state",
        "country",
        "source_provider",
        "created_at",
    ])
    
    from app.models.lead_contact import LeadContact, ContactType
    from app.models.lead_social_profile import LeadSocialProfile, SocialPlatform

    for lead_dict in leads:
        lead_id = lead_dict["id"]
        contacts = db.query(LeadContact).filter(LeadContact.lead_id == lead_id).all()
        socials = db.query(LeadSocialProfile).filter(LeadSocialProfile.lead_id == lead_id).all()

        phones = [c.normalized_value or c.original_value for c in contacts if c.contact_type == ContactType.PHONE]
        emails = [c.normalized_value or c.original_value for c in contacts if c.contact_type == ContactType.EMAIL]

        linkedin = next((s.profile_url for s in socials if s.platform == SocialPlatform.LINKEDIN), "")
        instagram = next((s.profile_url for s in socials if s.platform == SocialPlatform.INSTAGRAM), "")
        facebook = next((s.profile_url for s in socials if s.platform == SocialPlatform.FACEBOOK), "")
        twitter_x = next((s.profile_url for s in socials if s.platform == SocialPlatform.X), "")

        writer.writerow([
            lead_dict.get("business_name", ""),
            lead_dict.get("category", ""),
            phones[0] if phones else "",
            ", ".join(phones),
            emails[0] if emails else "",
            ", ".join(emails),
            lead_dict.get("website", ""),
            linkedin,
            instagram,
            facebook,
            twitter_x,
            lead_dict.get("address", ""),
            lead_dict.get("city", ""),
            lead_dict.get("state", ""),
            lead_dict.get("country", ""),
            lead_dict.get("source_provider", ""),
            lead_dict.get("created_at", ""),
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


@router.post("/verify-email")
def verify_email(email: str = Query(..., min_length=3)):
    """Verify an email address in real time using DNS MX and syntax checks."""
    from app.services.email_verifier import EmailVerifierService
    return EmailVerifierService.verify_email(email)


@router.post("/quick-scan", response_model=LeadDetailResponse)
async def quick_scan_business(
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    Directly scan any single business by name or website from multiple sources.
    """
    business_name = payload.get("business_name")
    website = payload.get("website")
    city = payload.get("city")
    category = payload.get("category", "General Business")
    ai_key = payload.get("ai_key")

    if not business_name and not website:
        raise HTTPException(status_code=400, detail="business_name or website is required")

    if not business_name and website:
        from urllib.parse import urlparse
        domain = urlparse(website).netloc or website
        business_name = domain.replace("www.", "").split(".")[0].capitalize()

    lead = await LeadService.create_or_update_lead(db, {
        "business_name": business_name,
        "website": website,
        "category": category,
        "city": city,
        "source_provider": "quick_scan",
    })

    try:
        await LeadService.enrich_lead(db, lead.id, custom_ai_key=ai_key)
    except Exception as e:
        print(f"[QuickScan] Enrichment warning: {e}")

    return lead


@router.post("/bulk-delete")
def bulk_delete_leads(
    payload: dict,
    db: Session = Depends(get_db),
):
    """Bulk delete leads by list of UUIDs."""
    lead_ids = payload.get("lead_ids", [])
    if not lead_ids:
        raise HTTPException(status_code=400, detail="lead_ids array is required")

    from app.models.business_lead import BusinessLead
    parsed_ids = [UUID(lid) for lid in lead_ids]
    deleted_count = db.query(BusinessLead).filter(BusinessLead.id.in_(parsed_ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"{deleted_count} leads deleted successfully", "count": deleted_count}


@router.get("/{lead_id}", response_model=LeadDetailResponse)
def get_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed lead information including contacts, social profiles, and source evidence.
    """
    lead = LeadService.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    from app.models.lead_contact import ContactType
    lead.email_count = sum(1 for c in lead.contacts if c.contact_type == ContactType.EMAIL)
    lead.phone_count = sum(1 for c in lead.contacts if c.contact_type == ContactType.PHONE)
    lead.social_count = len(lead.social_profiles)
    
    return lead


@router.post("/{lead_id}/enrich")
@router.post("/{lead_id}/scan")
async def enrich_lead(
    lead_id: UUID,
    ai_key: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Scan & enrich a single lead using multi-source extraction (Website + Search Radar + AI).
    """
    try:
        lead = await LeadService.enrich_lead(db, lead_id, custom_ai_key=ai_key)
        return {"message": "Lead enriched successfully", "lead_id": str(lead.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {str(e)}")


@router.delete("/{lead_id}")
def delete_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a single lead and cascade delete all its contacts and profiles."""
    lead = LeadService.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return {"message": "Lead deleted successfully", "id": str(lead_id)}


from app.services.lead_qualification_service import LeadQualificationService
from app.services.company_intelligence_service import CompanyIntelligenceService


@router.post("/{lead_id}/qualify")
async def qualify_lead(
    lead_id: UUID,
    payload: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
):
    """Run AI Lead Qualification against Ideal Customer Profile."""
    try:
        icp = payload.get("icp_profile")
        weights = payload.get("weights")
        result = await LeadQualificationService.qualify_lead(
            lead_id=str(lead_id),
            db=db,
            icp_profile=icp,
            custom_weights=weights,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qualification failed: {str(e)}")


@router.post("/{lead_id}/research")
async def research_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
):
    """Generate in-depth Company Intelligence research report with verified vs inferred separation."""
    try:
        report = await CompanyIntelligenceService.analyze_company(
            lead_id=str(lead_id),
            db=db,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.post("/{lead_id}/feedback")
def submit_qualification_feedback(
    lead_id: UUID,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """Manually correct qualification score or status with transparent audit logging."""
    try:
        res = LeadQualificationService.apply_manual_feedback(
            lead_id=str(lead_id),
            new_score=payload.get("new_score"),
            new_status=payload.get("new_status"),
            reason=payload.get("reason", "Manual user review adjustment"),
            db=db,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/manual")
async def create_manual_lead(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """Manually add a business lead to the discovery registry."""
    business_name = payload.get("business_name")
    if not business_name:
        raise HTTPException(status_code=400, detail="business_name is required")

    lead_data = {
        "business_name": business_name,
        "category": payload.get("category"),
        "website": payload.get("website"),
        "city": payload.get("city"),
        "state": payload.get("state"),
        "country": payload.get("country", "India"),
        "address": payload.get("address"),
        "description": payload.get("description"),
        "source_provider": "manual_entry",
        "provider_external_id": f"manual_{uuid.uuid4().hex[:12]}",
    }
    lead = await LeadService.create_or_update_lead(db, lead_data)

    # Add contacts if provided
    if payload.get("email"):
        from app.models.lead_contact import ContactType
        LeadService.add_contact(
            db,
            lead.id,
            ContactType.EMAIL,
            payload["email"],
            payload["email"].lower().strip(),
            "manual_verified",
        )
    if payload.get("phone"):
        from app.models.lead_contact import ContactType
        LeadService.add_contact(
            db,
            lead.id,
            ContactType.PHONE,
            payload["phone"],
            payload["phone"].strip(),
            "manual_verified",
        )

    db.commit()
    db.refresh(lead)
    return {"message": "Lead created successfully", "lead_id": str(lead.id)}


@router.post("/import/csv")
async def import_leads_csv(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """Import leads from tabular CSV JSON payload."""
    rows = payload.get("rows", [])
    if not rows:
        raise HTTPException(status_code=400, detail="rows array is required")

    imported = 0
    from app.models.lead_contact import ContactType
    for row in rows:
        name = row.get("business_name") or row.get("name") or row.get("company")
        if not name:
            continue
        lead_data = {
            "business_name": name,
            "category": row.get("category") or row.get("industry"),
            "website": row.get("website") or row.get("url"),
            "city": row.get("city"),
            "state": row.get("state"),
            "country": row.get("country", "India"),
            "source_provider": "csv_import",
            "provider_external_id": f"csv_{uuid.uuid4().hex[:12]}",
        }
        lead = await LeadService.create_or_update_lead(db, lead_data)

        email = row.get("email")
        if email:
            LeadService.add_contact(db, lead.id, ContactType.EMAIL, email, email.lower().strip(), "csv_imported")

        phone = row.get("phone")
        if phone:
            LeadService.add_contact(db, lead.id, ContactType.PHONE, phone, str(phone).strip(), "csv_imported")

        imported += 1

    db.commit()
    return {"message": f"Successfully imported {imported} leads from CSV", "count": imported}


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


