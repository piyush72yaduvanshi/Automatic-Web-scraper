"""Statistics endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.schemas.common import StatsResponse
from app.models import (
    BusinessLead,
    DiscoveryJob,
    LeadContact,
    LeadSocialProfile,
    ContactType,
    JobStatus,
)

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """
    Get platform statistics.
    
    Returns counts for leads, jobs, and extracted data.
    """
    # Total leads
    total_leads = db.query(func.count(BusinessLead.id)).scalar() or 0
    
    # Total jobs
    total_jobs = db.query(func.count(DiscoveryJob.id)).scalar() or 0
    
    # Jobs by status
    jobs_completed = db.query(func.count(DiscoveryJob.id)).filter(
        DiscoveryJob.status == JobStatus.COMPLETED
    ).scalar() or 0
    
    jobs_failed = db.query(func.count(DiscoveryJob.id)).filter(
        DiscoveryJob.status == JobStatus.FAILED
    ).scalar() or 0
    
    jobs_running = db.query(func.count(DiscoveryJob.id)).filter(
        DiscoveryJob.status == JobStatus.RUNNING
    ).scalar() or 0
    
    # Emails found
    emails_found = db.query(func.count(LeadContact.id)).filter(
        LeadContact.contact_type == ContactType.EMAIL
    ).scalar() or 0
    
    # Phones found
    phones_found = db.query(func.count(LeadContact.id)).filter(
        LeadContact.contact_type == ContactType.PHONE
    ).scalar() or 0
    
    # Social profiles found
    social_profiles_found = db.query(func.count(LeadSocialProfile.id)).scalar() or 0
    
    return {
        "total_leads": total_leads,
        "total_jobs": total_jobs,
        "emails_found": emails_found,
        "phones_found": phones_found,
        "social_profiles_found": social_profiles_found,
        "jobs_completed": jobs_completed,
        "jobs_failed": jobs_failed,
        "jobs_running": jobs_running,
    }
