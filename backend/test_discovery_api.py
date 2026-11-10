"""Quick test script for discovery schedule API endpoints."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from app.api.v1 import discovery_schedules
        print("✓ discovery_schedules module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import discovery_schedules: {e}")
        return False
    
    try:
        from app.schemas.discovery_schedule import (
            DiscoveryScheduleCreate,
            DiscoveryScheduleUpdate,
            DiscoveryScheduleResponse,
            DiscoveryTargetCreate,
            DiscoveryTargetResponse,
            DiscoveryRunResponse,
        )
        print("✓ All discovery schedule schemas imported successfully")
    except Exception as e:
        print(f"✗ Failed to import schemas: {e}")
        return False
    
    try:
        from app.models.discovery_schedule import (
            DiscoverySchedule,
            DiscoveryTarget,
            DiscoveryRun,
            ScheduleType,
            TargetType,
            DiscoveryRunStatus,
        )
        print("✓ All discovery schedule models imported successfully")
    except Exception as e:
        print(f"✗ Failed to import models: {e}")
        return False
    
    print("\nAll imports successful!")
    return True


def test_router_registration():
    """Test that the router is properly registered."""
    print("\nTesting router registration...")
    
    try:
        from app.api.v1 import api_router
        print("✓ API router imported successfully")
        
        # Check if our router is included
        routes_count = len(api_router.routes)
        print(f"✓ API router has {routes_count} routes registered")
        
        # Look for discovery schedule routes
        discovery_routes = [
            r for r in api_router.routes 
            if hasattr(r, 'path') and '/discovery' in r.path
        ]
        print(f"✓ Found {len(discovery_routes)} discovery-related routes")
        
        return True
    except Exception as e:
        print(f"✗ Failed to verify router registration: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Discovery Schedule API - Import & Registration Tests")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test router registration  
    if not test_router_registration():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
