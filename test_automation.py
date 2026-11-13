"""Quick test script to verify automation implementation."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("Testing automation implementation...")

# Test 1: Import models
try:
    from app.models.automation import AutomationSettings, LeadException
    print("✓ Automation models imported successfully")
except Exception as e:
    print(f"✗ Failed to import automation models: {e}")
    sys.exit(1)

# Test 2: Import services
try:
    from app.services.automation_settings_service import AutomationSettingsService
    from app.services.email_enrichment_service import EmailEnrichmentService
    from app.services.outreach_automation_service import OutreachAutomationService
    from app.services.crm_automation_service import CRMAutomationService
    from app.services.lead_automation_orchestrator import LeadAutomationOrchestrator
    print("✓ All automation services imported successfully")
except Exception as e:
    print(f"✗ Failed to import automation services: {e}")
    sys.exit(1)

# Test 3: Import API endpoints
try:
    from app.api.v1 import automation
    print("✓ Automation API router imported successfully")
except Exception as e:
    print(f"✗ Failed to import automation API: {e}")
    sys.exit(1)

# Test 4: Check migration file exists
migration_path = os.path.join(os.path.dirname(__file__), 'backend', 'alembic', 'versions', '20261113_0000_009_automation_tables.py')
if os.path.exists(migration_path):
    print("✓ Migration file exists")
else:
    print("✗ Migration file not found")
    sys.exit(1)

print("\n✅ All automation components verified successfully!")
print("\nNext steps:")
print("1. Start PostgreSQL database")
print("2. Run: cd backend && alembic upgrade head")
print("3. Start backend: cd backend && uvicorn main:app --reload")
print("4. Test bulk processing: POST /api/v1/leads/bulk-process")
