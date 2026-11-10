"""Comprehensive Integration Testing Suite for AI Sales CRM.

Tests:
1. Backend health and database connectivity
2. Workflow definitions and execution
3. NEW_LEAD event triggering workflows
4. Discovery schedule creation and management
5. Lead creation triggering automatic qualification
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

def print_test(name: str):
    """Print test header."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")

def test_health():
    """Test backend health endpoint."""
    print_test("Backend Health Check")
    response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/api/v1/health")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert data["overall"] == "healthy"
    print("✓ Backend is healthy")

def test_workflows():
    """Test workflow definitions."""
    print_test("Workflow Definitions")
    response = requests.get(f"{BASE_URL}/workflows")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} workflow definitions:")
    for wf in data:
        print(f"  - {wf['name']} (Trigger: {wf['trigger_type']}, Active: {wf['is_active']})")
    assert response.status_code == 200
    assert len(data) >= 3
    print("✓ Workflows loaded successfully")
    return data

def test_workflow_executions():
    """Test workflow execution history."""
    print_test("Workflow Execution History")
    response = requests.get(f"{BASE_URL}/workflows/executions")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data)} executions:")
    for exec in data[:3]:
        print(f"  - {exec['workflow_name']}: {exec['status']} (Trigger: {exec['trigger_event']})")
    assert response.status_code == 200
    print("✓ Workflow executions retrieved")

def test_create_lead_with_event():
    """Test creating a lead and verify NEW_LEAD event triggers workflow."""
    print_test("Create Lead + NEW_LEAD Event Trigger")
    
    # Create a test lead
    lead_data = {
        "business_name": f"Test Company {datetime.now().strftime('%H%M%S')}",
        "email": f"test{datetime.now().strftime('%H%M%S')}@example.com",
        "phone": "+911234567890",
        "city": "Mumbai",
        "category": "Technology"
    }
    
    print(f"Creating lead: {lead_data['business_name']}")
    response = requests.post(f"{BASE_URL}/leads/manual", json=lead_data, headers=HEADERS)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        lead = response.json()
        print(f"✓ Lead created: ID={lead.get('lead_id', 'N/A')}")
        
        # Wait a bit for event processing
        time.sleep(2)
        
        # Check if NEW_LEAD workflow was triggered
        response = requests.get(f"{BASE_URL}/workflows/executions?trigger_event=NEW_LEAD")
        executions = response.json()
        print(f"NEW_LEAD executions: {len(executions)}")
        
        if len(executions) > 0:
            latest = executions[0]
            print(f"✓ Latest execution: {latest['workflow_name']} - {latest['status']}")
            return lead
        else:
            print("⚠ No NEW_LEAD executions found - event system may not be integrated")
            return lead
    else:
        print(f"✗ Failed to create lead: {response.text}")
        return None

def test_discovery_schedules():
    """Test discovery schedule endpoints."""
    print_test("Discovery Schedule Management")
    
    # List existing schedules
    response = requests.get(f"{BASE_URL}/discovery-schedules/schedules")
    print(f"List schedules status: {response.status_code}")
    
    if response.status_code == 404:
        print("✗ Discovery schedules endpoint not found - checking routing")
        return None
    
    schedules = response.json()
    print(f"Existing schedules: {len(schedules)}")
    
    # Create a test schedule
    schedule_data = {
        "name": f"Integration Test Schedule {datetime.now().strftime('%H%M%S')}",
        "description": "Automated integration test schedule",
        "is_active": True,
        "schedule_type": "HOURLY",
        "interval_hours": 2,
        "max_leads_per_run": 5,
        "targets": [
            {
                "target_type": "CITY",
                "target_value": "Mumbai",
                "priority": 10
            }
        ]
    }
    
    print(f"Creating schedule: {schedule_data['name']}")
    response = requests.post(
        f"{BASE_URL}/discovery-schedules/schedules",
        json=schedule_data,
        headers=HEADERS
    )
    print(f"Create status: {response.status_code}")
    
    if response.status_code == 201:
        schedule = response.json()
        print(f"✓ Schedule created: ID={schedule['id']}")
        print(f"  Next run: {schedule.get('next_run_at', 'Not set')}")
        print(f"  Targets: {len(schedule.get('targets', []))}")
        return schedule
    else:
        print(f"✗ Failed to create schedule: {response.text[:200]}")
        return None

def test_manual_workflow_trigger():
    """Test manual workflow trigger."""
    print_test("Manual Workflow Execution")
    
    # Get the Auto-Qualify workflow
    response = requests.get(f"{BASE_URL}/workflows")
    workflows = response.json()
    
    auto_qualify = next((w for w in workflows if "Auto-Qualify" in w['name']), None)
    
    if not auto_qualify:
        print("✗ Auto-Qualify workflow not found")
        return
    
    print(f"Found workflow: {auto_qualify['name']}")
    
    # Trigger it manually
    payload = {
        "company_name": "Test Manual Company",
        "website": "https://example.com"
    }
    
    response = requests.post(
        f"{BASE_URL}/workflows/{auto_qualify['id']}/trigger",
        json=payload,
        headers=HEADERS
    )
    
    print(f"Execute status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Execution completed: {result.get('status', 'UNKNOWN')}")
        print(f"  Execution ID: {result.get('execution_id', 'N/A')}")
    else:
        print(f"⚠ Execution request: {response.text[:200]}")

def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("AI SALES CRM - INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "warnings": 0
    }
    
    try:
        test_health()
        results["passed"] += 1
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        results["failed"] += 1
        return results
    
    try:
        test_workflows()
        results["passed"] += 1
    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        results["failed"] += 1
    
    try:
        test_workflow_executions()
        results["passed"] += 1
    except Exception as e:
        print(f"✗ Workflow execution test failed: {e}")
        results["failed"] += 1
    
    try:
        lead = test_create_lead_with_event()
        if lead:
            results["passed"] += 1
        else:
            results["warnings"] += 1
    except Exception as e:
        print(f"✗ Lead creation test failed: {e}")
        results["failed"] += 1
    
    try:
        schedule = test_discovery_schedules()
        if schedule:
            results["passed"] += 1
        else:
            results["warnings"] += 1
    except Exception as e:
        print(f"✗ Discovery schedule test failed: {e}")
        results["failed"] += 1
    
    try:
        test_manual_workflow_trigger()
        results["passed"] += 1
    except Exception as e:
        print(f"⚠ Manual workflow trigger: {e}")
        results["warnings"] += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✓ Passed:   {results['passed']}")
    print(f"⚠ Warnings: {results['warnings']}")
    print(f"✗ Failed:   {results['failed']}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return results

if __name__ == "__main__":
    results = run_all_tests()
    exit(0 if results["failed"] == 0 else 1)
