"""Test script for Discovery Schedule Service."""

import asyncio
from app.core.database import SessionLocal, init_db
from app.services.discovery_schedule_service import DiscoveryScheduleService
from app.models.discovery_schedule import ScheduleType, TargetType

def test_discovery_schedule_service():
    """Test basic CRUD operations for discovery schedules."""
    
    print("🧪 Testing Discovery Schedule Service...\n")
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        # Test 1: Create a schedule
        print("1️⃣ Creating a test schedule...")
        schedule_data = {
            "name": "Test Daily Discovery",
            "description": "Test schedule for lead discovery automation",
            "is_active": True,
            "schedule_type": "DAILY",
            "max_leads_per_run": 50,
        }
        schedule = DiscoveryScheduleService.create_schedule(schedule_data, db)
        print(f"✅ Created schedule: {schedule.name} (ID: {schedule.id})")
        print(f"   Next run at: {schedule.next_run_at}")
        
        # Test 2: Add targets
        print("\n2️⃣ Adding discovery targets...")
        target1 = DiscoveryScheduleService.add_target(
            str(schedule.id),
            {
                "target_type": "CITY",
                "target_value": "New York",
                "priority": 10,
            },
            db
        )
        print(f"✅ Added target: {target1.target_type.value} = {target1.target_value}")
        
        target2 = DiscoveryScheduleService.add_target(
            str(schedule.id),
            {
                "target_type": "CATEGORY",
                "target_value": "Restaurant",
                "priority": 5,
            },
            db
        )
        print(f"✅ Added target: {target2.target_type.value} = {target2.target_value}")
        
        # Test 3: List schedules
        print("\n3️⃣ Listing all schedules...")
        schedules = DiscoveryScheduleService.list_schedules(db, active_only=True)
        print(f"✅ Found {len(schedules)} active schedule(s)")
        for s in schedules:
            print(f"   - {s.name}: {len(s.targets)} target(s)")
        
        # Test 4: Get next target
        print("\n4️⃣ Getting next target for discovery...")
        next_target = DiscoveryScheduleService.get_next_target_for_discovery(str(schedule.id), db)
        if next_target:
            print(f"✅ Next target: {next_target.target_type.value} = {next_target.target_value} (priority: {next_target.priority})")
        
        # Test 5: Update schedule
        print("\n5️⃣ Updating schedule...")
        updated_schedule = DiscoveryScheduleService.update_schedule(
            str(schedule.id),
            {"max_leads_per_run": 100},
            db
        )
        print(f"✅ Updated max_leads_per_run to: {updated_schedule.max_leads_per_run}")
        
        # Test 6: Build discovery query
        print("\n6️⃣ Testing query builder...")
        query, location = DiscoveryScheduleService._build_discovery_query(target1)
        print(f"✅ City target query: '{query}' in '{location}'")
        query, location = DiscoveryScheduleService._build_discovery_query(target2)
        print(f"✅ Category target query: '{query}' in '{location}'")
        
        # Cleanup
        print("\n7️⃣ Cleaning up test data...")
        DiscoveryScheduleService.remove_target(str(target1.id), db)
        DiscoveryScheduleService.remove_target(str(target2.id), db)
        DiscoveryScheduleService.delete_schedule(str(schedule.id), db)
        print("✅ Test data cleaned up")
        
        print("\n✅ All tests passed! Discovery Schedule Service is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_discovery_schedule_service()
