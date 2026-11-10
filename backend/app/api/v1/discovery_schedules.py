"""Discovery Schedule Management REST API Endpoints.

Comprehensive CRUD operations for discovery schedule automation, target management,
manual discovery triggers, and run history tracking.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.discovery_schedule import (
    DiscoverySchedule,
    DiscoveryTarget,
    DiscoveryRun,
    ScheduleType,
    TargetType,
    DiscoveryRunStatus,
)
from app.schemas.discovery_schedule import (
    DiscoveryScheduleCreate,
    DiscoveryScheduleUpdate,
    DiscoveryScheduleResponse,
    DiscoveryTargetCreate,
    DiscoveryTargetResponse,
    DiscoveryRunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/discovery",
    tags=["Discovery Automation"],
    dependencies=[Depends(verify_api_key)]
)


def calculate_next_run(schedule: DiscoverySchedule) -> Optional[datetime]:
    """Calculate next run time based on schedule type."""
    now = datetime.utcnow()
    
    if not schedule.is_active:
        return None
    
    if schedule.schedule_type == ScheduleType.HOURLY:
        hours = schedule.interval_hours or 1
        return now + timedelta(hours=hours)
    elif schedule.schedule_type == ScheduleType.DAILY:
        return now + timedelta(days=1)
    elif schedule.schedule_type == ScheduleType.WEEKLY:
        return now + timedelta(weeks=1)
    elif schedule.schedule_type == ScheduleType.CUSTOM:
        # For CUSTOM, cron_expression should be parsed by scheduler
        # For now, default to 1 day
        return now + timedelta(days=1)
    
    return now + timedelta(days=1)


# ==================== Discovery Schedule CRUD ====================

@router.post("/schedules", response_model=DiscoveryScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_discovery_schedule(
    schedule_data: DiscoveryScheduleCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new discovery schedule with targets.
    
    - **name**: Unique name for the schedule
    - **description**: Optional description
    - **schedule_type**: HOURLY, DAILY, WEEKLY, or CUSTOM
    - **is_active**: Enable/disable schedule (default: True)
    - **max_leads_per_run**: Maximum leads to discover per run
    - **targets**: List of discovery targets (cities, industries, etc.)
    """
    try:
        # Create schedule
        schedule = DiscoverySchedule(
            name=schedule_data.name,
            description=schedule_data.description,
            is_active=schedule_data.is_active,
            schedule_type=schedule_data.schedule_type,
            cron_expression=schedule_data.cron_expression,
            interval_hours=schedule_data.interval_hours,
            max_leads_per_run=schedule_data.max_leads_per_run,
        )
        
        # Calculate next run time
        schedule.next_run_at = calculate_next_run(schedule)
        
        db.add(schedule)
        db.flush()  # Get schedule.id
        
        # Add targets
        for target_data in schedule_data.targets:
            target = DiscoveryTarget(
                schedule_id=schedule.id,
                target_type=target_data.target_type,
                target_value=target_data.target_value,
                priority=target_data.priority,
            )
            db.add(target)
        
        db.commit()
        db.refresh(schedule)
        
        logger.info(f"Created discovery schedule: {schedule.name} (ID: {schedule.id})")
        return schedule
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating discovery schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create discovery schedule: {str(e)}"
        )


@router.get("/schedules", response_model=List[DiscoveryScheduleResponse])
def list_discovery_schedules(
    active_only: bool = Query(False, description="Filter active schedules only"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List all discovery schedules with their targets.
    
    - **active_only**: Filter only active schedules
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    try:
        query = db.query(DiscoverySchedule)
        
        if active_only:
            query = query.filter(DiscoverySchedule.is_active == True)
        
        schedules = query.order_by(desc(DiscoverySchedule.created_at)).offset(skip).limit(limit).all()
        
        return schedules
        
    except Exception as e:
        logger.error(f"Error listing discovery schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list discovery schedules: {str(e)}"
        )


@router.get("/schedules/{schedule_id}", response_model=DiscoveryScheduleResponse)
def get_discovery_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a specific discovery schedule by ID with all targets.
    """
    try:
        schedule = db.query(DiscoverySchedule).filter(DiscoverySchedule.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery schedule not found: {schedule_id}"
            )
        
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discovery schedule {schedule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get discovery schedule: {str(e)}"
        )


@router.put("/schedules/{schedule_id}", response_model=DiscoveryScheduleResponse)
def update_discovery_schedule(
    schedule_id: UUID,
    schedule_data: DiscoveryScheduleUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing discovery schedule.
    
    Only provided fields will be updated. Null/missing fields are ignored.
    """
    try:
        schedule = db.query(DiscoverySchedule).filter(DiscoverySchedule.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery schedule not found: {schedule_id}"
            )
        
        # Update fields if provided
        update_data = schedule_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        # Recalculate next_run_at if schedule type or interval changed
        if any(k in update_data for k in ['schedule_type', 'interval_hours', 'is_active']):
            schedule.next_run_at = calculate_next_run(schedule)
        
        schedule.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(schedule)
        
        logger.info(f"Updated discovery schedule: {schedule.name} (ID: {schedule_id})")
        return schedule
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating discovery schedule {schedule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update discovery schedule: {str(e)}"
        )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discovery_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Delete a discovery schedule and all associated targets and runs.
    
    This operation is irreversible. CASCADE delete will remove all targets and runs.
    """
    try:
        schedule = db.query(DiscoverySchedule).filter(DiscoverySchedule.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery schedule not found: {schedule_id}"
            )
        
        logger.info(f"Deleting discovery schedule: {schedule.name} (ID: {schedule_id})")
        
        db.delete(schedule)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting discovery schedule {schedule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete discovery schedule: {str(e)}"
        )


# ==================== Discovery Target Management ====================

@router.post("/schedules/{schedule_id}/targets", response_model=DiscoveryTargetResponse, status_code=status.HTTP_201_CREATED)
def add_discovery_target(
    schedule_id: UUID,
    target_data: DiscoveryTargetCreate,
    db: Session = Depends(get_db),
):
    """
    Add a new discovery target to an existing schedule.
    
    - **target_type**: CITY, STATE, COUNTRY, INDUSTRY, or CATEGORY
    - **target_value**: The value (e.g., "New York", "Technology", "Restaurant")
    - **priority**: Higher priority targets are processed first
    """
    try:
        # Verify schedule exists
        schedule = db.query(DiscoverySchedule).filter(DiscoverySchedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery schedule not found: {schedule_id}"
            )
        
        # Create target
        target = DiscoveryTarget(
            schedule_id=schedule_id,
            target_type=target_data.target_type,
            target_value=target_data.target_value,
            priority=target_data.priority,
        )
        
        db.add(target)
        db.commit()
        db.refresh(target)
        
        logger.info(f"Added target {target_data.target_type}:{target_data.target_value} to schedule {schedule_id}")
        return target
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding discovery target to schedule {schedule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add discovery target: {str(e)}"
        )


@router.get("/schedules/{schedule_id}/targets", response_model=List[DiscoveryTargetResponse])
def list_discovery_targets(
    schedule_id: UUID,
    target_type: Optional[TargetType] = Query(None, description="Filter by target type"),
    db: Session = Depends(get_db),
):
    """
    List all discovery targets for a specific schedule.
    
    Optionally filter by target type (CITY, STATE, COUNTRY, INDUSTRY, CATEGORY).
    """
    try:
        # Verify schedule exists
        schedule = db.query(DiscoverySchedule).filter(DiscoverySchedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery schedule not found: {schedule_id}"
            )
        
        query = db.query(DiscoveryTarget).filter(DiscoveryTarget.schedule_id == schedule_id)
        
        if target_type:
            query = query.filter(DiscoveryTarget.target_type == target_type)
        
        targets = query.order_by(desc(DiscoveryTarget.priority), DiscoveryTarget.created_at).all()
        
        return targets
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing discovery targets for schedule {schedule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list discovery targets: {str(e)}"
        )


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discovery_target(
    target_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Delete a specific discovery target by ID.
    """
    try:
        target = db.query(DiscoveryTarget).filter(DiscoveryTarget.id == target_id).first()
        
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery target not found: {target_id}"
            )
        
        logger.info(f"Deleting discovery target {target.target_type}:{target.target_value} (ID: {target_id})")
        
        db.delete(target)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting discovery target {target_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete discovery target: {str(e)}"
        )


# ==================== Discovery Run Management ====================

@router.post("/schedules/{schedule_id}/run", response_model=DiscoveryRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_discovery_run(
    schedule_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Manually trigger a discovery run for a specific schedule.
    
    This will execute the discovery immediately with all configured targets,
    regardless of the schedule's next_run_at time.
    """
    try:
        schedule = db.query(DiscoverySchedule).filter(DiscoverySchedule.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery schedule not found: {schedule_id}"
            )
        
        # Get all targets for this schedule
        targets = db.query(DiscoveryTarget).filter(DiscoveryTarget.schedule_id == schedule_id).all()
        
        if not targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot run discovery: No targets configured for this schedule"
            )
        
        # Create target snapshot
        target_snapshot = {
            "targets": [
                {
                    "type": t.target_type.value,
                    "value": t.target_value,
                    "priority": t.priority
                }
                for t in targets
            ],
            "max_leads_per_run": schedule.max_leads_per_run,
            "triggered_by": "MANUAL",
        }
        
        # Create discovery run record
        run = DiscoveryRun(
            schedule_id=schedule_id,
            status=DiscoveryRunStatus.RUNNING,
            target_snapshot=target_snapshot,
            started_at=datetime.utcnow(),
        )
        
        db.add(run)
        
        # Update schedule last_run_at
        schedule.last_run_at = datetime.utcnow()
        
        db.commit()
        db.refresh(run)
        
        logger.info(f"Manual discovery run triggered for schedule {schedule.name} (Run ID: {run.id})")
        
        # TODO: Trigger actual discovery worker/task here
        # For now, we just create the run record
        # In production, this would dispatch to Celery/background worker
        
        return run
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error triggering manual discovery run for schedule {schedule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger discovery run: {str(e)}"
        )


@router.get("/runs", response_model=List[DiscoveryRunResponse])
def list_discovery_runs(
    schedule_id: Optional[UUID] = Query(None, description="Filter by schedule ID"),
    status: Optional[DiscoveryRunStatus] = Query(None, description="Filter by run status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    List discovery run history with optional filters.
    
    - **schedule_id**: Filter runs for a specific schedule
    - **status**: Filter by run status (RUNNING, COMPLETED, FAILED)
    - **skip/limit**: Pagination
    """
    try:
        query = db.query(DiscoveryRun)
        
        if schedule_id:
            query = query.filter(DiscoveryRun.schedule_id == schedule_id)
        
        if status:
            query = query.filter(DiscoveryRun.status == status)
        
        runs = query.order_by(desc(DiscoveryRun.started_at)).offset(skip).limit(limit).all()
        
        return runs
        
    except Exception as e:
        logger.error(f"Error listing discovery runs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list discovery runs: {str(e)}"
        )


@router.get("/runs/{run_id}", response_model=DiscoveryRunResponse)
def get_discovery_run(
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific discovery run.
    
    Includes target snapshot, results, and error details if failed.
    """
    try:
        run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discovery run not found: {run_id}"
            )
        
        return run
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discovery run {run_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get discovery run: {str(e)}"
        )
