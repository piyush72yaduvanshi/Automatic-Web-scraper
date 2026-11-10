# Discovery Schedule API - Testing Guide

## Overview
This document provides comprehensive test cases for all discovery schedule management endpoints.

## Prerequisites
1. Backend server running on `http://localhost:8000`
2. PostgreSQL database with discovery_schedules, discovery_targets, and discovery_runs tables
3. API key (if AUTH_ENABLED=true): Set `X-API-Key` header

## Base URL
```
http://localhost:8000/api/v1/discovery
```

## Endpoint Summary

### Discovery Schedules (5 endpoints)
- `POST /schedules` - Create a new discovery schedule
- `GET /schedules` - List all discovery schedules
- `GET /schedules/{schedule_id}` - Get specific schedule details
- `PUT /schedules/{schedule_id}` - Update a schedule
- `DELETE /schedules/{schedule_id}` - Delete a schedule

### Discovery Targets (3 endpoints)
- `POST /schedules/{schedule_id}/targets` - Add a target to a schedule
- `GET /schedules/{schedule_id}/targets` - List all targets for a schedule
- `DELETE /targets/{target_id}` - Delete a specific target

### Discovery Runs (3 endpoints)
- `POST /schedules/{schedule_id}/run` - Manually trigger a discovery run
- `GET /runs` - List all discovery runs (with filters)
- `GET /runs/{run_id}` - Get specific run details

---

## Test Cases

### 1. Create Discovery Schedule

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/discovery/schedules" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm" \
  -d '{
    "name": "Daily Tech Startup Discovery",
    "description": "Discover technology startups in major US cities",
    "is_active": true,
    "schedule_type": "DAILY",
    "max_leads_per_run": 100,
    "targets": [
      {
        "target_type": "CITY",
        "target_value": "San Francisco",
        "priority": 10
      },
      {
        "target_type": "INDUSTRY",
        "target_value": "Technology",
        "priority": 8
      }
    ]
  }'
```

**Expected Response (201):**
```json
{
  "id": "uuid-here",
  "name": "Daily Tech Startup Discovery",
  "description": "Discover technology startups in major US cities",
  "is_active": true,
  "schedule_type": "DAILY",
  "cron_expression": null,
  "interval_hours": null,
  "max_leads_per_run": 100,
  "last_run_at": null,
  "next_run_at": "2024-01-02T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "targets": [
    {
      "id": "target-uuid-1",
      "schedule_id": "uuid-here",
      "target_type": "CITY",
      "target_value": "San Francisco",
      "priority": 10,
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": "target-uuid-2",
      "schedule_id": "uuid-here",
      "target_type": "INDUSTRY",
      "target_value": "Technology",
      "priority": 8,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### 2. List Discovery Schedules

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/discovery/schedules?active_only=true&limit=10" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (200):**
```json
[
  {
    "id": "uuid-here",
    "name": "Daily Tech Startup Discovery",
    "description": "Discover technology startups in major US cities",
    "is_active": true,
    "schedule_type": "DAILY",
    "max_leads_per_run": 100,
    "last_run_at": null,
    "next_run_at": "2024-01-02T12:00:00Z",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "targets": [...]
  }
]
```

### 3. Get Specific Schedule

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/discovery/schedules/{schedule_id}" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (200):** Same as create response

**Error Case (404):**
```json
{
  "detail": "Discovery schedule not found: {schedule_id}"
}
```

### 4. Update Discovery Schedule

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/v1/discovery/schedules/{schedule_id}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm" \
  -d '{
    "name": "Updated Schedule Name",
    "is_active": false,
    "max_leads_per_run": 200
  }'
```

**Expected Response (200):** Updated schedule object

### 5. Delete Discovery Schedule

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/discovery/schedules/{schedule_id}" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (204):** No content

### 6. Add Discovery Target

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/discovery/schedules/{schedule_id}/targets" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm" \
  -d '{
    "target_type": "CITY",
    "target_value": "New York",
    "priority": 9
  }'
```

**Expected Response (201):**
```json
{
  "id": "target-uuid",
  "schedule_id": "schedule-uuid",
  "target_type": "CITY",
  "target_value": "New York",
  "priority": 9,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 7. List Discovery Targets

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/discovery/schedules/{schedule_id}/targets?target_type=CITY" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (200):** Array of target objects

### 8. Delete Discovery Target

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/discovery/targets/{target_id}" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (204):** No content

### 9. Trigger Manual Discovery Run

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/discovery/schedules/{schedule_id}/run" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (202):**
```json
{
  "id": "run-uuid",
  "schedule_id": "schedule-uuid",
  "status": "RUNNING",
  "leads_discovered": 0,
  "target_snapshot": {
    "targets": [
      {
        "type": "CITY",
        "value": "San Francisco",
        "priority": 10
      }
    ],
    "max_leads_per_run": 100,
    "triggered_by": "MANUAL"
  },
  "error_message": null,
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": null
}
```

**Error Case (400):**
```json
{
  "detail": "Cannot run discovery: No targets configured for this schedule"
}
```

### 10. List Discovery Runs

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/discovery/runs?schedule_id={schedule_id}&status=COMPLETED&limit=20" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (200):**
```json
[
  {
    "id": "run-uuid",
    "schedule_id": "schedule-uuid",
    "status": "COMPLETED",
    "leads_discovered": 45,
    "target_snapshot": {...},
    "error_message": null,
    "started_at": "2024-01-01T12:00:00Z",
    "completed_at": "2024-01-01T12:05:30Z"
  }
]
```

### 11. Get Specific Discovery Run

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/discovery/runs/{run_id}" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (200):** Run object with full details

---

## Workflow Execution History Endpoint

### Get Workflow Executions with Filters

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/workflows/executions?trigger_event=NEW_LEAD&status=COMPLETED&limit=20" \
  -H "X-API-Key: dev-admin-key-ai-sales-crm"
```

**Expected Response (200):**
```json
[
  {
    "id": "execution-uuid",
    "workflow_id": "workflow-uuid",
    "workflow_name": "Auto-Qualify Newly Discovered Leads",
    "trigger_event": "NEW_LEAD",
    "status": "COMPLETED",
    "current_step_id": "qualify",
    "retry_count": 0,
    "start_time": "2024-01-01T12:00:00Z",
    "completion_time": "2024-01-01T12:00:30Z",
    "error_info": null,
    "step_results": {
      "research": {
        "status": "SUCCESS",
        "research": {...}
      },
      "qualify": {
        "status": "SUCCESS",
        "qualification": {...}
      }
    },
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

---

## Testing with Postman

1. Import the following collection structure:
   - Create a new collection: "Discovery Schedule API"
   - Add environment variables:
     - `base_url`: `http://localhost:8000`
     - `api_key`: `dev-admin-key-ai-sales-crm`
     - `schedule_id`: (set dynamically from create response)
     - `target_id`: (set dynamically from create target response)
     - `run_id`: (set dynamically from trigger run response)

2. Add pre-request script to automatically set API key header:
   ```javascript
   pm.request.headers.add({
       key: 'X-API-Key',
       value: pm.environment.get('api_key')
   });
   ```

3. Add test scripts to extract IDs:
   ```javascript
   // For create schedule endpoint
   if (pm.response.code === 201) {
       pm.environment.set('schedule_id', pm.response.json().id);
   }
   ```

---

## Testing in Browser (Swagger UI)

1. Navigate to: `http://localhost:8000/docs`
2. Click "Authorize" button at the top
3. Enter API key: `dev-admin-key-ai-sales-crm`
4. Navigate to "Discovery Automation" section
5. Try each endpoint interactively

---

## Error Codes Reference

| Code | Description |
|------|-------------|
| 200 | Success - Resource returned |
| 201 | Created - New resource created |
| 202 | Accepted - Request accepted for processing |
| 204 | No Content - Resource deleted |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing API key |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Request validation failed |
| 500 | Internal Server Error - Server error occurred |

---

## Target Types Reference

| Type | Description | Example Values |
|------|-------------|----------------|
| CITY | Target a specific city | "San Francisco", "New York", "London" |
| STATE | Target a state/province | "California", "Texas", "Ontario" |
| COUNTRY | Target a country | "United States", "Canada", "United Kingdom" |
| INDUSTRY | Target an industry | "Technology", "Healthcare", "Finance" |
| CATEGORY | Target a business category | "Restaurant", "SaaS", "E-commerce" |

---

## Schedule Types Reference

| Type | Description | Configuration |
|------|-------------|---------------|
| HOURLY | Runs every N hours | Set `interval_hours` (1-168) |
| DAILY | Runs once per day | No extra config needed |
| WEEKLY | Runs once per week | No extra config needed |
| CUSTOM | Custom cron schedule | Set `cron_expression` |

---

## Discovery Run Status Reference

| Status | Description |
|--------|-------------|
| RUNNING | Discovery is currently in progress |
| COMPLETED | Discovery completed successfully |
| FAILED | Discovery failed with errors |

