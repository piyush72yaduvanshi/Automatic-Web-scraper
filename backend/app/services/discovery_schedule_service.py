"""Discovery Schedule Service for automated lead discovery.

Manages scheduled discovery automation with configurable targets and execution tracking.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.discovery_schedule import (
    DiscoverySchedule,
    DiscoveryTarget,
    DiscoveryRun,
    ScheduleType,
    TargetType,
    DiscoveryRunStatus,
)
from app.services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)


class DiscoveryScheduleService:
    """Service for managing scheduled discovery automation."""
    
    @staticmethod
    def create_schedule(data: Dict[str, Any], db: Session) -> DiscoverySchedule:
        """
        Create a new discovery schedule.
        
        Args:
            data: Schedule configuration with fields:
                - name: Schedule name
                - description: Optional description
                - is_active: Whether schedule is active
                - schedule_type: HOURLY, DAILY, WEEKLY, or CUSTOM
                - cron_expression: For CUSTOM schedules
                - interval_hours: For HOURLY schedules
                - max_leads_per_run: Maximum leads per execution
            db: Database session
        
        Returns:
            Created DiscoverySchedule
        """
        schedule = DiscoverySchedule(
            name=data.get("name"),
            description=data.get("description"),
            is_active=data.get("is_active", True),
            schedule_type=ScheduleType(data.get("schedule_type", "DAILY")),
            cron_expression=data.get("cron_expression"),
            interval_hours=data.get("interval_hours"),
            max_leads_per_run=data.get("max_leads_per_run", 50),
            next_run_at=DiscoveryScheduleService._calculate_next_run(
                ScheduleType(data.get("schedule_type", "DAILY")),
                data.get("interval_hours"),
                data.get("cron_expression")
            ),
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        logger.info(f"Created discovery schedule: {schedule.name} (ID: {schedule.id})")
        return schedule
    
    @staticmethod
    def list_schedules(db: Session, active_only: bool = False) -> List[DiscoverySchedule]:
        """
        List all discovery schedules.
        
        Args:
            db: Database session
            active_only: If True, only return active schedules
        
        Returns:
            List of DiscoverySchedule objects
        """
        query = db.query(DiscoverySchedule)
        
        if active_only:
            query = query.filter(DiscoverySchedule.is_active == True)
        
        return query.order_by(DiscoverySchedule.created_at.desc()).all()
    
    @staticmethod
    def update_schedule(schedule_id: str, data: Dict[str, Any], db: Session) -> DiscoverySchedule:
        """
        Update an existing discovery schedule.
        
        Args:
            schedule_id: Schedule UUID
            data: Updated fields
            db: Database session
        
        Returns:
            Updated DiscoverySchedule
        
        Raises:
            ValueError: If schedule not found
        """
        schedule = db.query(DiscoverySchedule).filter(
            DiscoverySchedule.id == UUID(schedule_id)
        ).first()
        
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Update fields
        if "name" in data:
            schedule.name = data["name"]
        if "description" in data:
            schedule.description = data["description"]
        if "is_active" in data:
            schedule.is_active = data["is_active"]
        if "schedule_type" in data:
            schedule.schedule_type = ScheduleType(data["schedule_type"])
        if "cron_expression" in data:
            schedule.cron_expression = data["cron_expression"]
        if "interval_hours" in data:
            schedule.interval_hours = data["interval_hours"]
        if "max_leads_per_run" in data:
            schedule.max_leads_per_run = data["max_leads_per_run"]
        
        # Recalculate next_run_at if schedule parameters changed
        if any(k in data for k in ["schedule_type", "interval_hours", "cron_expression"]):
            schedule.next_run_at = DiscoveryScheduleService._calculate_next_run(
                schedule.schedule_type,
                schedule.interval_hours,
                schedule.cron_expression
            )
        
        db.commit()
        db.refresh(schedule)
        
        logger.info(f"Updated discovery schedule: {schedule.name} (ID: {schedule.id})")
        return schedule
    
    @staticmethod
    def delete_schedule(schedule_id: str, db: Session) -> bool:
        """
        Delete a discovery schedule.
        
        Args:
            schedule_id: Schedule UUID
            db: Database session
        
        Returns:
            True if deleted, False if not found
        """
        schedule = db.query(DiscoverySchedule).filter(
            DiscoverySchedule.id == UUID(schedule_id)
        ).first()
        
        if not schedule:
            return False
        
        db.delete(schedule)
        db.commit()
        
        logger.info(f"Deleted discovery schedule: {schedule.name} (ID: {schedule_id})")
        return True
    
    @staticmethod
    def add_target(schedule_id: str, target_data: Dict[str, Any], db: Session) -> DiscoveryTarget:
        """
        Add a discovery target to a schedule.
        
        Args:
            schedule_id: Schedule UUID
            target_data: Target configuration with fields:
                - target_type: CITY, STATE, COUNTRY, INDUSTRY, or CATEGORY
                - target_value: Target value (e.g., "New York", "Technology")
                - priority: Target priority (higher = processed first)
            db: Database session
        
        Returns:
            Created DiscoveryTarget
        
        Raises:
            ValueError: If schedule not found
        """
        schedule = db.query(DiscoverySchedule).filter(
            DiscoverySchedule.id == UUID(schedule_id)
        ).first()
        
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        target = DiscoveryTarget(
            schedule_id=schedule.id,
            target_type=TargetType(target_data.get("target_type")),
            target_value=target_data.get("target_value"),
            priority=target_data.get("priority", 0),
        )
        
        db.add(target)
        db.commit()
        db.refresh(target)
        
        logger.info(
            f"Added target to schedule {schedule.name}: "
            f"{target.target_type.value}={target.target_value}"
        )
        return target
    
    @staticmethod
    def remove_target(target_id: str, db: Session) -> bool:
        """
        Remove a discovery target.
        
        Args:
            target_id: Target UUID
            db: Database session
        
        Returns:
            True if deleted, False if not found
        """
        target = db.query(DiscoveryTarget).filter(
            DiscoveryTarget.id == UUID(target_id)
        ).first()
        
        if not target:
            return False
        
        db.delete(target)
        db.commit()
        
        logger.info(f"Removed discovery target: {target_id}")
        return True
    
    @staticmethod
    def get_next_target_for_discovery(schedule_id: str, db: Session) -> Optional[DiscoveryTarget]:
        """
        Get the next target to process for discovery (highest priority first).
        
        Args:
            schedule_id: Schedule UUID
            db: Database session
        
        Returns:
            DiscoveryTarget or None if no targets exist
        """
        return db.query(DiscoveryTarget).filter(
            DiscoveryTarget.schedule_id == UUID(schedule_id)
        ).order_by(
            DiscoveryTarget.priority.desc(),
            DiscoveryTarget.created_at.asc()
        ).first()
    
    @staticmethod
    async def execute_discovery_run(schedule_id: str, db: Session) -> DiscoveryRun:
        """
        Execute a discovery run for a schedule.
        
        Args:
            schedule_id: Schedule UUID
            db: Database session
        
        Returns:
            Created DiscoveryRun with results
        
        Raises:
            ValueError: If schedule not found or no targets configured
        """
        schedule = db.query(DiscoverySchedule).filter(
            DiscoverySchedule.id == UUID(schedule_id)
        ).first()
        
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        # Get all targets ordered by priority
        targets = db.query(DiscoveryTarget).filter(
            DiscoveryTarget.schedule_id == schedule.id
        ).order_by(
            DiscoveryTarget.priority.desc(),
            DiscoveryTarget.created_at.asc()
        ).all()
        
        if not targets:
            raise ValueError(f"No targets configured for schedule {schedule.name}")
        
        # Create discovery run record
        run = DiscoveryRun(
            schedule_id=schedule.id,
            status=DiscoveryRunStatus.RUNNING,
            target_snapshot=[
                {
                    "target_type": t.target_type.value,
                    "target_value": t.target_value,
                    "priority": t.priority,
                }
                for t in targets
            ],
            started_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        logger.info(
            f"Starting discovery run {run.id} for schedule {schedule.name} "
            f"with {len(targets)} targets"
        )
        
        total_leads_discovered = 0
        errors = []
        
        try:
            # Process each target respecting max_leads_per_run
            for target in targets:
                if total_leads_discovered >= schedule.max_leads_per_run:
                    logger.info(
                        f"Reached max_leads_per_run limit ({schedule.max_leads_per_run}), "
                        f"stopping early"
                    )
                    break
                
                # Calculate remaining capacity
                remaining_capacity = schedule.max_leads_per_run - total_leads_discovered
                
                try:
                    # Build discovery query based on target type
                    query, location = DiscoveryScheduleService._build_discovery_query(target)
                    
                    logger.info(
                        f"Discovering leads: query='{query}', location='{location}', "
                        f"limit={remaining_capacity}"
                    )
                    
                    # Execute discovery using existing DiscoveryService
                    result = await DiscoveryService.execute_scan_stream(
                        db=db,
                        query=query,
                        location=location,
                        limit=min(remaining_capacity, 20),  # Reasonable batch size
                        preferred_provider="serpapi",
                    )
                    
                    # Consume the async generator to execute discovery
                    leads_from_target = 0
                    async for event_data in result:
                        # Count leads as they're discovered
                        if "lead_ready" in event_data:
                            leads_from_target += 1
                    
                    total_leads_discovered += leads_from_target
                    logger.info(
                        f"Discovered {leads_from_target} leads from target "
                        f"{target.target_type.value}={target.target_value}"
                    )
                    
                except Exception as e:
                    error_msg = f"Error discovering for target {target.target_value}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update run status
            run.status = DiscoveryRunStatus.COMPLETED
            run.leads_discovered = total_leads_discovered
            run.completed_at = datetime.utcnow()
            
            if errors:
                run.error_message = "; ".join(errors)
            
            # Update schedule execution tracking
            schedule.last_run_at = datetime.utcnow()
            schedule.next_run_at = DiscoveryScheduleService._calculate_next_run(
                schedule.schedule_type,
                schedule.interval_hours,
                schedule.cron_expression,
                from_time=schedule.last_run_at
            )
            
            db.commit()
            db.refresh(run)
            
            logger.info(
                f"Completed discovery run {run.id}: "
                f"discovered {total_leads_discovered} leads, "
                f"next run at {schedule.next_run_at}"
            )
            
            return run
            
        except Exception as e:
            # Mark run as failed
            run.status = DiscoveryRunStatus.FAILED
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(run)
            
            logger.error(f"Discovery run {run.id} failed: {str(e)}")
            raise
    
    @staticmethod
    def _build_discovery_query(target: DiscoveryTarget) -> tuple[str, str]:
        """
        Build discovery query and location from target configuration.
        
        Args:
            target: DiscoveryTarget
        
        Returns:
            Tuple of (query, location)
        """
        if target.target_type == TargetType.CITY:
            # City target: discover businesses in that city
            return "business", target.target_value
        
        elif target.target_type == TargetType.STATE:
            # State target: discover businesses in major cities of that state
            return "business", target.target_value
        
        elif target.target_type == TargetType.COUNTRY:
            # Country target: discover businesses in that country
            return "business", target.target_value
        
        elif target.target_type == TargetType.INDUSTRY:
            # Industry target: discover businesses in that industry
            return f"{target.target_value} companies", ""
        
        elif target.target_type == TargetType.CATEGORY:
            # Category target: discover businesses in that category
            return target.target_value, ""
        
        else:
            # Fallback: generic business search
            return target.target_value, ""
    
    @staticmethod
    def _calculate_next_run(
        schedule_type: ScheduleType,
        interval_hours: Optional[int] = None,
        cron_expression: Optional[str] = None,
        from_time: Optional[datetime] = None,
    ) -> datetime:
        """
        Calculate next run time based on schedule configuration.
        
        Args:
            schedule_type: Type of schedule
            interval_hours: Hours between runs (for HOURLY)
            cron_expression: Cron expression (for CUSTOM)
            from_time: Base time for calculation (default: now)
        
        Returns:
            Next run datetime
        """
        base_time = from_time or datetime.utcnow()
        
        if schedule_type == ScheduleType.HOURLY:
            hours = interval_hours or 1
            return base_time + timedelta(hours=hours)
        
        elif schedule_type == ScheduleType.DAILY:
            # Run once per day at the same hour as initial creation
            return base_time + timedelta(days=1)
        
        elif schedule_type == ScheduleType.WEEKLY:
            # Run once per week at the same time
            return base_time + timedelta(weeks=1)
        
        elif schedule_type == ScheduleType.CUSTOM:
            # For CUSTOM schedules with cron, we'd need croniter library
            # For now, default to daily
            # TODO: Implement croniter integration
            logger.warning("CUSTOM schedules not fully implemented, defaulting to daily")
            return base_time + timedelta(days=1)
        
        else:
            # Default to daily
            return base_time + timedelta(days=1)
