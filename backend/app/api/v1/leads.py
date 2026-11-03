"""Leads API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
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

    lead = LeadService.create_or_update_lead(db, {
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

