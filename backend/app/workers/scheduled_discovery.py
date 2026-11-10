"""Celery tasks for scheduled discovery automation.

Provides background workers for executing scheduled lead discovery runs.
"""

import asyncio
import logging
from datetime import datetime
from celery import Task
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.discovery_schedule import DiscoverySchedule, DiscoveryRunStatus
from app.services.discovery_schedule_service import DiscoveryScheduleService

logger = logging.getLogger(__name__)

# Concurrency control: max concurrent discoveries
MAX_CONCURRENT_DISCOVERIES = 3
_running_discoveries = 0
_discovery_lock = asyncio.Lock()


class DatabaseTask(Task):
    """Base task with database session management."""
    
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


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.scheduled_discovery.check_and_run_scheduled_discoveries"
)
def check_and_run_scheduled_discoveries(self):
    """
    Celery Beat task that checks for due discovery schedules and executes them.
    
    This task runs periodically (every 5 minutes by default) and:
    1. Queries for active schedules where next_run_at <= now
    2. For each due schedule, spawns a discovery execution task
    3. Respects concurrency limits (max 3 concurrent discoveries)
    
    Returns:
        dict: Execution summary
    """
    try:
        db = self.session
        now = datetime.utcnow()
        
        # Query active schedules that are due to run
        due_schedules = db.query(DiscoverySchedule).filter(
            DiscoverySchedule.is_active == True,
            DiscoverySchedule.next_run_at <= now
        ).all()
        
        if not due_schedules:
            logger.info("No due discovery schedules found")
            return {"status": "success", "due_schedules": 0, "triggered": 0}
        
        logger.info(f"Found {len(due_schedules)} due discovery schedules")
        
        triggered = 0
        skipped = 0
        errors = []
        
        for schedule in due_schedules:
            try:
                # Check concurrency limit
                running_count = db.query(DiscoverySchedule).join(
                    DiscoverySchedule.runs
                ).filter(
                    DiscoverySchedule.runs.any(status=DiscoveryRunStatus.RUNNING)
                ).count()
                
                if running_count >= MAX_CONCURRENT_DISCOVERIES:
                    logger.warning(
                        f"Skipping schedule {schedule.name}: "
                        f"concurrent limit reached ({running_count}/{MAX_CONCURRENT_DISCOVERIES})"
                    )
                    skipped += 1
                    continue
                
                # Spawn async task to run discovery for this schedule
                logger.info(f"Triggering discovery for schedule: {schedule.name} (ID: {schedule.id})")
                run_discovery_for_schedule.delay(str(schedule.id))
                triggered += 1
                
            except Exception as e:
                error_msg = f"Error triggering schedule {schedule.name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            "status": "success",
            "timestamp": now.isoformat(),
            "due_schedules": len(due_schedules),
            "triggered": triggered,
            "skipped": skipped,
            "errors": errors if errors else None,
        }
        
        logger.info(
            f"Check complete: {triggered} triggered, {skipped} skipped "
            f"(concurrency limit: {MAX_CONCURRENT_DISCOVERIES})"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to check scheduled discoveries: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.scheduled_discovery.run_discovery_for_schedule",
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def run_discovery_for_schedule(self, schedule_id: str):
    """
    Execute discovery for a specific schedule.
    
    This task can be called manually via API or automatically by the beat scheduler.
    It executes the full discovery run for all configured targets, respecting
    the schedule's max_leads_per_run limit.
    
    Args:
        schedule_id: UUID of the DiscoverySchedule to execute
    
    Returns:
        dict: Execution result with discovery stats
    """
    try:
        db = self.session
        
        logger.info(f"Starting discovery run for schedule ID: {schedule_id}")
        
        # Verify schedule exists and is active
        schedule = db.query(DiscoverySchedule).filter(
            DiscoverySchedule.id == schedule_id
        ).first()
        
        if not schedule:
            error_msg = f"Schedule {schedule_id} not found"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "schedule_id": schedule_id,
            }
        
        if not schedule.is_active:
            logger.warning(f"Schedule {schedule.name} is not active, skipping")
            return {
                "status": "skipped",
                "reason": "schedule_inactive",
                "schedule_id": schedule_id,
                "schedule_name": schedule.name,
            }
        
        # Execute discovery run asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            run = loop.run_until_complete(
                DiscoveryScheduleService.execute_discovery_run(schedule_id, db)
            )
            
            result = {
                "status": "success",
                "schedule_id": schedule_id,
                "schedule_name": schedule.name,
                "run_id": str(run.id),
                "leads_discovered": run.leads_discovered,
                "run_status": run.status.value,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
            }
            
            if run.error_message:
                result["warnings"] = run.error_message
            
            logger.info(
                f"✅ Discovery run {run.id} completed for schedule {schedule.name}: "
                f"{run.leads_discovered} leads discovered"
            )
            
            return result
            
        finally:
            loop.close()
    
    except Exception as e:
        error_msg = f"Discovery run failed for schedule {schedule_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Retry with exponential backoff if retriable error
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying discovery run (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        
        return {
            "status": "error",
            "error": str(e),
            "schedule_id": schedule_id,
            "retries": self.request.retries,
        }


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.scheduled_discovery.trigger_manual_discovery"
)
def trigger_manual_discovery(self, schedule_id: str):
    """
    Manually trigger a discovery run for a schedule (bypasses next_run_at check).
    
    This is useful for testing schedules or running them on-demand from the UI.
    
    Args:
        schedule_id: UUID of the DiscoverySchedule to execute
    
    Returns:
        dict: Execution result
    """
    logger.info(f"Manual discovery trigger for schedule: {schedule_id}")
    
    # Delegate to the main run task
    result = run_discovery_for_schedule.delay(schedule_id)
    
    return {
        "status": "triggered",
        "schedule_id": schedule_id,
        "task_id": result.id,
        "message": "Discovery run triggered successfully",
    }
