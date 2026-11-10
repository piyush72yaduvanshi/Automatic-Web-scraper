"""Discovery API endpoints."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.core.config import settings
from app.schemas.discovery import (
    DiscoveryJobCreate,
    DiscoveryJobResponse,
    DiscoveryJobDetail,
    DiscoveryJobListResponse,
)
from app.models.discovery_job import JobStatus
from app.services import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["discovery"])


async def _execute_job_in_background(job_id: UUID, custom_ai_key: Optional[str] = None):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        await DiscoveryService.execute_job(db, job_id, custom_ai_key)
    except Exception as e:
        print(f"[BackgroundTask] Error executing job {job_id}: {e}")
    finally:
        db.close()


@router.post("/jobs", response_model=DiscoveryJobResponse)
@limiter.limit(settings.RATE_LIMIT_DISCOVERY)
async def create_discovery_job(
    request: Request,
    job_data: DiscoveryJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new business discovery job.
    The job will be executed in the background and you can track its progress.
    """
    job = DiscoveryService.create_job(db, job_data)
    background_tasks.add_task(_execute_job_in_background, job.id)
    return job


@router.get("/jobs", response_model=DiscoveryJobListResponse)
def list_discovery_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[JobStatus] = None,
    db: Session = Depends(get_db),
):
    """List discovery jobs with pagination and filtering."""
    skip = (page - 1) * page_size
    jobs, total = DiscoveryService.list_jobs(db, skip=skip, limit=page_size, status=status)
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/jobs/{job_id}", response_model=DiscoveryJobDetail)
def get_discovery_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    """Get discovery job status and details."""
    job = DiscoveryService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/jobs/{job_id}")
def delete_discovery_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a discovery job by ID."""
    job = DiscoveryService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted successfully", "id": str(job_id)}


@router.get("/scan/stream")
@limiter.limit(settings.RATE_LIMIT_DISCOVERY)
async def stream_discovery_scan(
    request: Request,
    query: str = Query(..., min_length=1, description="Business category or keyword"),
    location: str = Query(..., min_length=1, description="City, state, country"),
    limit: int = Query(10, ge=1, le=50, description="Max businesses to scan"),
    provider: str = Query("serpapi", description="Discovery provider: serpapi, apify, or multi"),
    ai_key: Optional[str] = Query(None, description="Optional Gemini or OpenRouter key"),
    db: Session = Depends(get_db),
):
    """
    Live real-time scan streaming via Server-Sent Events (SSE).
    Streams discovery progress, live leads, and multi-source enrichment events immediately!
    """
    return StreamingResponse(
        DiscoveryService.execute_scan_stream(
            db=db,
            query=query,
            location=location,
            limit=limit,
            preferred_provider=provider,
            custom_ai_key=ai_key,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/scan")
@limiter.limit(settings.RATE_LIMIT_DISCOVERY)
async def quick_scan(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """
    Fast synchronous discovery and enrichment scan.
    """
    query = payload.get("query")
    location = payload.get("location")
    limit = int(payload.get("limit", 10))
    provider = payload.get("provider", "serpapi")
    ai_key = payload.get("ai_key")

    if not query or not location:
        raise HTTPException(status_code=400, detail="query and location are required")

    from app.providers.discovery.orchestrator import MultiSourceDiscoveryOrchestrator
    from app.providers.enrichment.multi_source_enricher import MultiSourceEnricher
    from app.services.lead_service import LeadService

    orchestrator = MultiSourceDiscoveryOrchestrator()
    disc_res = await orchestrator.discover_businesses(
        query=query,
        location=location,
        limit=limit,
        preferred_provider=provider,
    )

    businesses = disc_res.get("businesses", [])
    enricher = MultiSourceEnricher()
    enriched_leads = []

    for b_data in businesses:
        lead = LeadService.create_or_update_lead(db, b_data)
        enriched = await enricher.enrich_lead(
            business_name=lead.business_name,
            website=lead.website,
            category=lead.category,
            city=lead.city,
            state=lead.state,
            existing_phone=b_data.get("phone"),
            custom_ai_key=ai_key,
        )
        LeadService.add_enrichment_data(db, lead.id, enriched)
        enriched_leads.append({
            "id": str(lead.id),
            "business_name": lead.business_name,
            "category": lead.category,
            "description": lead.description,
            "address": lead.address,
            "city": lead.city,
            "state": lead.state,
            "country": lead.country,
            "website": lead.website,
            "source_provider": lead.source_provider,
            "emails": enriched.get("emails", []),
            "phones": enriched.get("phones", []),
            "social_profiles": enriched.get("social_profiles", []),
            "quality_score": enriched.get("quality_score", 60),
            "sources_consulted": enriched.get("sources_consulted", []),
        })

    return {
        "status": "success",
        "total_found": len(businesses),
        "total_enriched": len(enriched_leads),
        "leads": enriched_leads,
    }
