"""Celery tasks for background processing."""

import asyncio
from uuid import UUID
from celery import Task
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.services import DiscoveryService


class DatabaseTask(Task):
    """Base task with database session."""
    
    _session = None
    
    @property
    def session(self):
        if self._session is None:
            self._session = SessionLocal()
        return self._session
    
    def after_return(self, *args, **kwargs):
        if self._session is not None:
            self._session.close()
            self._session = None


@celery_app.task(bind=True, base=DatabaseTask, name="app.workers.tasks.execute_discovery_job")
def execute_discovery_job(self, job_id: str):
    """
    Execute a discovery job in background.
    
    Args:
        job_id: UUID of the discovery job
    """
    try:
        # Convert string to UUID
        job_uuid = UUID(job_id)
        
        # Get database session
        db = self.session
        
        # Execute job asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            job = loop.run_until_complete(
                DiscoveryService.execute_job(db, job_uuid)
            )
            return {
                "status": "success",
                "job_id": str(job.id),
                "total_found": job.total_found,
                "total_enriched": job.total_enriched
            }
        finally:
            loop.close()
            
    except Exception as e:
        # Log error
        print(f"Job {job_id} failed: {str(e)}")
        raise
