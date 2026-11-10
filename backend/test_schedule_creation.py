"""Test discovery schedule creation."""

import asyncio
import sys
sys.path.insert(0, "d:/MVP/backend")

from app.core.database import SessionLocal, init_db
from app.services.discovery_schedule_service import DiscoveryScheduleService
from app.models.discovery_schedule import ScheduleType, TargetType

async def test_schedule_creation():
    """Test creating a discovery schedule."""
    init_db()
    db = SessionLocal()
    
    try:
        print("Creating discovery schedule...")
        schedule_data = {
            "name": "Test Mumbai Discovery",
            "description": "Automated discovery for Mumbai tech companies",
            "is_active": True,
            "schedule_type": ScheduleType.HOURLY,
            "interval_hours": 2,
            "max_leads_per_run": 10,
            "targets": [
                {
                    "target_type": TargetType.CITY,
                    "target_value": "Mumbai",
                    "priority": 10,
                },
                {
                    "target_type": TargetType.INDUSTRY,
                    "target_value": "Technology",
                    "priority": 8,
                }
            ]
        }
        
        schedule = DiscoveryScheduleService.create_schedule(schedule_data, db)
        print(f"✓ Created schedule: {schedule.name} (ID: {schedule.id})")
        print(f"  Schedule type: {schedule.schedule_type.value}")
        print(f"  Next run at: {schedule.next_run_at}")
        print(f"  Targets: {len(schedule.targets)}")
        
        for target in schedule.targets:
            print(f"    - {target.target_type.value}: {target.target_value}")
        
        # List all schedules
        print("\nListing all schedules:")
        schedules = DiscoveryScheduleService.list_schedules(db)
        print(f"Total schedules: {len(schedules)}")
        for s in schedules:
            print(f"  - {s['name']} (Active: {s['is_active']})")
        
        print("\n✓ Test completed successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_schedule_creation())
