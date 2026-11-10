"""Discovery service for managing business discovery operations."""

from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from uuid import UUID
import json
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import DiscoveryJob, JobStatus, BusinessLead, LeadContact, ContactType, LeadSocialProfile
from app.schemas.discovery import DiscoveryJobCreate
from app.providers.discovery.orchestrator import MultiSourceDiscoveryOrchestrator
from app.providers.enrichment.multi_source_enricher import MultiSourceEnricher
from app.services.lead_service import LeadService


class DiscoveryService:
    """Service for business discovery operations."""
    
    @staticmethod
    def create_job(db: Session, job_data: DiscoveryJobCreate) -> DiscoveryJob:
        """Create a new discovery job."""
        provider_name = job_data.preferred_provider or "serpapi"
        
        job = DiscoveryJob(
            search_query=job_data.query,
            location=job_data.location,
            radius_km=job_data.radius_km,
            requested_limit=job_data.limit,
            provider=provider_name,
            status=JobStatus.QUEUED,
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return job
    
    @staticmethod
    def get_job(db: Session, job_id: UUID) -> Optional[DiscoveryJob]:
        """Get job by ID."""
        return db.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
    
    @staticmethod
    def list_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[JobStatus] = None,
    ) -> tuple[List[DiscoveryJob], int]:
        """List discovery jobs with pagination."""
        query = db.query(DiscoveryJob)
        
        if status:
            query = query.filter(DiscoveryJob.status == status)
        
        total = query.count()
        jobs = query.order_by(desc(DiscoveryJob.created_at)).offset(skip).limit(limit).all()
        
        return jobs, total
    
    @staticmethod
    def update_job_status(
        db: Session,
        job_id: UUID,
        status: JobStatus,
        error_message: Optional[str] = None,
        provider_job_id: Optional[str] = None,
    ) -> Optional[DiscoveryJob]:
        """Update job status."""
        job = DiscoveryService.get_job(db, job_id)
        if not job:
            return None
        
        job.status = status
        if error_message:
            job.error_message = error_message
        if provider_job_id:
            job.provider_job_id = provider_job_id
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def update_job_counts(
        db: Session,
        job_id: UUID,
        total_found: int,
        total_enriched: int,
    ) -> Optional[DiscoveryJob]:
        """Update job result counts."""
        job = DiscoveryService.get_job(db, job_id)
        if not job:
            return None
        
        job.total_found = total_found
        job.total_enriched = total_enriched
        
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    async def execute_job(db: Session, job_id: UUID, custom_ai_key: Optional[str] = None) -> DiscoveryJob:
        """
        Execute a discovery job using multi-source discovery & multi-source enrichment.
        """
        job = DiscoveryService.get_job(db, job_id)
        if not job:
            raise ValueError("Job not found")
        
        job = DiscoveryService.update_job_status(db, job_id, JobStatus.RUNNING)
        
        try:
            orchestrator = MultiSourceDiscoveryOrchestrator()
            if not orchestrator.is_configured():
                raise ValueError("No discovery providers are configured")
            
            result = await orchestrator.discover_businesses(
                query=job.search_query,
                location=job.location,
                radius_km=job.radius_km,
                limit=job.requested_limit,
                preferred_provider=job.provider,
            )
            
            businesses = result.get("businesses", [])
            provider_job_id = result.get("provider_job_id")
            
            # Immediately update job with total_found so UI reflects discovery instantly!
            job.total_found = len(businesses)
            if provider_job_id:
                job.provider_job_id = provider_job_id
            db.commit()
            db.refresh(job)
            
            enricher = MultiSourceEnricher()
            total_enriched = 0
            
            for b_data in businesses:
                lead = await LeadService.create_or_update_lead(db, b_data)
                
                try:
                    enriched_data = await enricher.enrich_lead(
                        business_name=lead.business_name,
                        website=lead.website,
                        category=lead.category,
                        city=lead.city,
                        state=lead.state,
                        existing_phone=b_data.get("phone"),
                        custom_ai_key=custom_ai_key,
                    )
                    
                    if enriched_data.get("emails") or enriched_data.get("phones") or enriched_data.get("social_profiles"):
                        LeadService.add_enrichment_data(db, lead.id, enriched_data)
                        total_enriched += 1
                        # Incrementally update count so /jobs shows live progress
                        job.total_enriched = total_enriched
                        db.commit()
                except Exception as e:
                    print(f"Enrichment error for {lead.business_name}: {e}")
            
            DiscoveryService.update_job_counts(db, job_id, len(businesses), total_enriched)
            job = DiscoveryService.update_job_status(db, job_id, JobStatus.COMPLETED)
            return job
            
        except Exception as e:
            job = DiscoveryService.update_job_status(
                db,
                job_id,
                JobStatus.FAILED,
                error_message=str(e)
            )
            raise

    @staticmethod
    async def execute_scan_stream(
        db: Session,
        query: str,
        location: str,
        limit: int = 15,
        preferred_provider: str = "serpapi",
        custom_ai_key: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream discovery and multi-source enrichment events via Server-Sent Events (SSE).
        Yields events in real time as leads are discovered, crawled, and analyzed.
        """
        def sse(event_type: str, data: Dict[str, Any]) -> str:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        yield sse("status", {
            "step": "init",
            "message": f"🚀 Initializing multi-source scan for '{query}' in '{location}'..."
        })
        await asyncio.sleep(0.1)

        try:
            # Create DiscoveryJob record so live scan is tracked across Jobs and Dashboard!
            live_job = DiscoveryJob(
                search_query=query,
                location=location,
                requested_limit=limit,
                provider=f"{preferred_provider}",
                status=JobStatus.RUNNING,
                total_found=0,
                total_enriched=0,
            )
            db.add(live_job)
            db.commit()
            db.refresh(live_job)

            orchestrator = MultiSourceDiscoveryOrchestrator()
            yield sse("status", {
                "step": "discovery",
                "message": f"🔍 Querying Google Maps & Local Business radar via {preferred_provider.upper()}..."
            })

            disc_res = await orchestrator.discover_businesses(
                query=query,
                location=location,
                limit=limit,
                preferred_provider=preferred_provider,
            )

            businesses = disc_res.get("businesses", [])
            live_job.total_found = len(businesses)
            db.commit()

            yield sse("discovered", {
                "step": "found_candidates",
                "count": len(businesses),
                "message": f"📍 Discovered {len(businesses)} verified business candidates. Starting multi-source contact extraction...",
            })

            enricher = MultiSourceEnricher()
            total_enriched = 0

            # Process candidates and yield each one immediately as it completes
            for idx, b_data in enumerate(businesses):
                business_name = b_data.get("business_name", "Unknown")
                yield sse("status", {
                    "step": "enriching",
                    "current": idx + 1,
                    "total": len(businesses),
                    "message": f"⚡ Extracting contacts & footprint for [{idx+1}/{len(businesses)}]: {business_name}..."
                })

                # Create/save lead in DB
                lead = await LeadService.create_or_update_lead(db, b_data)

                # Enrich via multi-source engine
                try:
                    enriched = await enricher.enrich_lead(
                        business_name=lead.business_name,
                        website=lead.website,
                        category=lead.category,
                        city=lead.city,
                        state=lead.state,
                        existing_phone=b_data.get("phone"),
                        custom_ai_key=custom_ai_key,
                    )

                    LeadService.add_enrichment_data(db, lead.id, enriched)
                    total_enriched += 1

                    live_job.total_enriched = total_enriched
                    db.commit()

                    # Fetch updated counts and details
                    email_count = len(enriched.get("emails", []))
                    phone_count = len(enriched.get("phones", []))
                    social_count = len(enriched.get("social_profiles", []))

                    lead_payload = {
                        "id": str(lead.id),
                        "business_name": lead.business_name,
                        "category": lead.category,
                        "description": lead.description or enriched.get("summary"),
                        "address": lead.address,
                        "city": lead.city,
                        "state": lead.state,
                        "country": lead.country,
                        "website": lead.website,
                        "source_provider": lead.source_provider,
                        "email_count": email_count,
                        "phone_count": phone_count,
                        "social_count": social_count,
                        "emails": enriched.get("emails", []),
                        "phones": enriched.get("phones", []),
                        "social_profiles": enriched.get("social_profiles", []),
                        "quality_score": enriched.get("quality_score", 60),
                        "sources_consulted": enriched.get("sources_consulted", []),
                        "key_people": enriched.get("key_people", []),
                    }

                    yield sse("lead_ready", {
                        "lead": lead_payload,
                        "message": f"✅ Enriched {business_name} ({email_count} emails, {phone_count} phones, {social_count} socials, Score: {enriched.get('quality_score')}%)"
                    })

                except Exception as ex:
                    print(f"Error enriching lead {lead.business_name}: {ex}")
                    # Still yield discovered lead even if enrichment had partial failure
                    yield sse("lead_ready", {
                        "lead": {
                            "id": str(lead.id),
                            "business_name": lead.business_name,
                            "category": lead.category,
                            "description": lead.description,
                            "address": lead.address,
                            "city": lead.city,
                            "website": lead.website,
                            "source_provider": lead.source_provider,
                            "email_count": 0,
                            "phone_count": 1 if b_data.get("phone") else 0,
                            "social_count": 0,
                            "quality_score": 40,
                            "emails": [],
                            "phones": [{"normalized": b_data.get("phone")}] if b_data.get("phone") else [],
                            "social_profiles": [],
                            "sources_consulted": ["Basic Listing"],
                        },
                        "message": f"⚠️ Found basic info for {business_name}"
                    })

            # Mark live job completed
            live_job.status = JobStatus.COMPLETED
            live_job.completed_at = datetime.utcnow()
            live_job.total_found = len(businesses)
            live_job.total_enriched = total_enriched
            db.commit()

            yield sse("complete", {
                "step": "finished",
                "total_found": len(businesses),
                "total_enriched": total_enriched,
                "message": f"🎉 Scan complete! Successfully processed {len(businesses)} leads with {total_enriched} fully enriched."
            })

        except Exception as e:
            if 'live_job' in locals() and live_job:
                try:
                    live_job.status = JobStatus.FAILED
                    live_job.error_message = str(e)
                    db.commit()
                except Exception:
                    pass

            yield sse("error", {
                "message": f"Scan failed: {str(e)}"
            })
