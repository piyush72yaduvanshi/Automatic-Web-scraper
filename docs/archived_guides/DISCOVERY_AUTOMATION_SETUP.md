# 🚀 Discovery Automation - Complete Setup Guide

**Complete guide for setting up and running the automated lead discovery system.**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Component Configuration](#component-configuration)
5. [Running the System](#running-the-system)
6. [API Usage Examples](#api-usage-examples)
7. [Troubleshooting](#troubleshooting)
8. [Architecture Details](#architecture-details)

---

## 🎯 System Overview

The Discovery Automation system enables:
- **Scheduled Discovery**: Automatic lead discovery at configured intervals (hourly, daily, weekly, custom)
- **Geo-Targeting**: City, state, and country-based targeting
- **Industry Filtering**: Discover leads in specific industries or categories
- **Event-Driven Workflows**: Automatic lead qualification and CRM sync via events
- **Manual Triggers**: On-demand discovery runs via UI or API

### Key Features
✅ Multi-target scheduling (combine cities, industries, categories)  
✅ Priority-based target processing  
✅ Run history and audit logging  
✅ Real-time workflow monitoring  
✅ Configurable lead limits per run  
✅ Cron expression support for complex schedules  

---

## 🔧 Prerequisites

### Required Software
- **Python 3.11+** with virtual environment
- **Node.js 18+** and npm
- **Docker & Docker Compose** (for PostgreSQL + Redis)
- **Redis** (for Celery task queue)
- **PostgreSQL 16** with pgvector extension

### Required API Keys
Configure these in your `.env` file:
```env
# Discovery Providers
APIFY_API_TOKEN=your_apify_token
SCRAPLING_API_KEY=your_scrapling_key

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/crm_leads

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-min-32-chars
API_KEY=test-api-key-2025
```

---

## ⚡ Quick Start

### 1. Start Docker Services
```powershell
# Start PostgreSQL + Redis
cd d:\MVP
docker compose -f docker-compose.test.yml up -d

# Verify containers are running
docker ps

# Enable pgvector extension
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Setup Backend
```powershell
# Navigate to backend
cd d:\MVP\backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

### 3. Start Backend Server
```powershell
# From d:\MVP\backend with venv activated
python main.py

# Backend will start on: http://localhost:8000
# API Docs available at: http://localhost:8000/docs
```

### 4. Start Frontend
```powershell
# Open new terminal
cd d:\MVP\frontend

# Install dependencies (if not already installed)
npm install

# Start dev server
npm run dev

# Frontend will start on: http://localhost:5173 or 5174
```

### 5. Start Celery Workers (For Automation)
```powershell
# Terminal 3: Celery Worker
cd d:\MVP\backend
.\venv\Scripts\Activate.ps1
celery -A app.workers.celery_app worker --loglevel=info -P solo

# Terminal 4: Celery Beat (Scheduler)
cd d:\MVP\backend
.\venv\Scripts\Activate.ps1
celery -A app.workers.celery_app beat --loglevel=info
```

**System should now be fully operational!** 🎉

---

## 🔧 Component Configuration

### PostgreSQL Configuration
**Docker Container:** `crm_leads_postgres`  
**Port:** 5432  
**Database:** crm_leads  
**User:** postgres  
**Password:** postgres  

**Extensions Required:**
- pgvector (v0.8.6+) - For vector similarity search

### Redis Configuration
**Docker Container:** `crm_leads_redis`  
**Port:** 6379  
**Database:** 0 (default)  

**Used For:**
- Celery task queue
- Celery result backend
- Rate limiting (optional)

### Celery Configuration
**Location:** `backend/celeryconfig.py`

**Beat Schedule:**
```python
# Runs every 5 minutes to check for scheduled discoveries
'check-scheduled-discoveries': {
    'task': 'app.workers.scheduled_discovery.execute_scheduled_discovery_task',
    'schedule': crontab(minute='*/5'),
}

# Cleanup old runs daily at 2 AM
'cleanup-old-discovery-runs': {
    'task': 'app.workers.scheduled_discovery.cleanup_old_discovery_runs_task',
    'schedule': crontab(hour=2, minute=0),
}
```

**To Customize:**
Edit `backend/celeryconfig.py` and restart Celery beat.

---

## 🚀 Running the System

### Development Mode

#### Terminal Layout
```
Terminal 1: Docker Containers (PostgreSQL + Redis)
Terminal 2: Backend API Server (FastAPI)
Terminal 3: Frontend Dev Server (Vite + React)
Terminal 4: Celery Worker
Terminal 5: Celery Beat Scheduler
```

#### Startup Commands
```powershell
# Terminal 1
docker compose -f docker-compose.test.yml up

# Terminal 2
cd d:\MVP\backend
.\venv\Scripts\python.exe main.py

# Terminal 3
cd d:\MVP\frontend
npm run dev

# Terminal 4
cd d:\MVP\backend
.\venv\Scripts\celery.exe -A app.workers.celery_app worker -l info -P solo

# Terminal 5
cd d:\MVP\backend
.\venv\Scripts\celery.exe -A app.workers.celery_app beat -l info
```

### Production Mode

#### Using Process Managers

**Option 1: Windows Services**
Convert Python scripts to Windows services using `nssm` or similar tools.

**Option 2: Supervisor (WSL/Linux)**
```ini
[program:crm_backend]
command=/path/to/venv/bin/python main.py
directory=/path/to/backend
autostart=true
autorestart=true

[program:crm_celery_worker]
command=/path/to/venv/bin/celery -A app.workers.celery_app worker
directory=/path/to/backend
autostart=true
autorestart=true

[program:crm_celery_beat]
command=/path/to/venv/bin/celery -A app.workers.celery_app beat
directory=/path/to/backend
autostart=true
autorestart=true
```

**Frontend:**
```powershell
# Build for production
cd d:\MVP\frontend
npm run build

# Serve with nginx, IIS, or static host
# Build output: frontend/dist/
```

---

## 📡 API Usage Examples

### Authentication
All API requests require the `X-API-Key` header:
```powershell
$headers = @{
    "X-API-Key" = "test-api-key-2025"
    "Content-Type" = "application/json"
}
```

### Create Discovery Schedule

**Scenario:** Discover restaurants in Mumbai every day at 9 AM

```powershell
$body = @{
    name = "Daily Mumbai Restaurants"
    description = "Discover new restaurant leads in Mumbai"
    is_active = $true
    schedule_type = "DAILY"
    max_leads_per_run = 50
    targets = @(
        @{
            target_type = "CITY"
            target_value = "Mumbai"
            priority = 1
        },
        @{
            target_type = "CATEGORY"
            target_value = "Restaurant"
            priority = 1
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Daily Mumbai Restaurants",
  "is_active": true,
  "schedule_type": "DAILY",
  "next_run_at": "2026-11-11T09:00:00",
  "max_leads_per_run": 50,
  "targets": [
    {
      "id": "uuid",
      "target_type": "CITY",
      "target_value": "Mumbai",
      "priority": 1
    },
    {
      "id": "uuid",
      "target_type": "CATEGORY",
      "target_value": "Restaurant",
      "priority": 1
    }
  ]
}
```

### Hourly Schedule with Interval

**Scenario:** Discover tech companies in Bangalore every 3 hours

```powershell
$body = @{
    name = "Bangalore Tech Companies - Every 3 Hours"
    description = "High-frequency discovery for tech leads"
    is_active = $true
    schedule_type = "HOURLY"
    interval_hours = 3
    max_leads_per_run = 25
    targets = @(
        @{
            target_type = "CITY"
            target_value = "Bangalore"
            priority = 1
        },
        @{
            target_type = "INDUSTRY"
            target_value = "Technology"
            priority = 1
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

### Custom Cron Schedule

**Scenario:** Run every Monday and Friday at 10:30 AM

```powershell
$body = @{
    name = "Bi-weekly Discovery"
    description = "Runs Monday and Friday mornings"
    is_active = $true
    schedule_type = "CUSTOM"
    cron_expression = "30 10 * * 1,5"  # Min Hour Day Month DayOfWeek
    max_leads_per_run = 100
    targets = @(
        @{
            target_type = "COUNTRY"
            target_value = "India"
            priority = 1
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

### List All Schedules

```powershell
# Get all schedules
Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules" `
    -Method GET `
    -Headers $headers

# Get only active schedules
Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules?active_only=true" `
    -Method GET `
    -Headers $headers
```

### Manual Trigger

```powershell
$scheduleId = "your-schedule-uuid"

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules/$scheduleId/run" `
    -Method POST `
    -Headers $headers
```

**Response:**
```json
{
  "id": "run-uuid",
  "schedule_id": "schedule-uuid",
  "status": "RUNNING",
  "started_at": "2026-11-10T18:26:00",
  "target_snapshot": {
    "targets": [...],
    "max_leads_per_run": 50,
    "triggered_by": "MANUAL"
  }
}
```

### Get Run History

```powershell
# All runs
Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/runs?limit=20" `
    -Method GET `
    -Headers $headers

# Runs for specific schedule
$scheduleId = "your-schedule-uuid"
Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/runs?schedule_id=$scheduleId" `
    -Method GET `
    -Headers $headers

# Only failed runs
Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/runs?status=FAILED" `
    -Method GET `
    -Headers $headers
```

### Update Schedule

```powershell
$scheduleId = "your-schedule-uuid"
$body = @{
    is_active = $false  # Pause schedule
    max_leads_per_run = 100  # Increase limit
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules/$scheduleId" `
    -Method PUT `
    -Headers $headers `
    -Body $body
```

### Add/Remove Targets

**Add Target:**
```powershell
$scheduleId = "your-schedule-uuid"
$body = @{
    target_type = "INDUSTRY"
    target_value = "Healthcare"
    priority = 2
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/schedules/$scheduleId/targets" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

**Remove Target:**
```powershell
$targetId = "target-uuid"

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/discovery-schedules/targets/$targetId" `
    -Method DELETE `
    -Headers $headers
```

---

## 🐛 Troubleshooting

### Backend Won't Start

**Symptom:** `ModuleNotFoundError` or import errors

**Solution:**
```powershell
cd d:\MVP\backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# If specific modules missing:
pip install slowapi sentry-sdk[fastapi] prometheus-fastapi-instrumentator
```

### Database Connection Errors

**Symptom:** `could not connect to server` or connection timeout

**Check Docker:**
```powershell
docker ps  # Verify postgres container is running
docker logs crm_leads_postgres  # Check for errors
```

**Restart PostgreSQL:**
```powershell
docker compose -f docker-compose.test.yml restart postgres
```

**Verify Extension:**
```powershell
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c "\dx"
```

### Celery Workers Not Starting

**Symptom:** `celery: command not found` or worker crashes

**Solution:**
```powershell
# Install Celery in venv
pip install celery[redis]

# Windows requires solo pool
celery -A app.workers.celery_app worker -P solo --loglevel=info

# Check Redis connection
redis-cli -h localhost -p 6379 ping
```

### Schedules Not Executing

**Check Celery Beat is Running:**
```powershell
# Should see periodic log entries
celery -A app.workers.celery_app beat --loglevel=debug
```

**Verify Schedule Status:**
```sql
-- Check next_run_at times
SELECT id, name, is_active, next_run_at, last_run_at 
FROM discovery_schedules 
WHERE is_active = true;
```

**Force Manual Run:**
```powershell
# Use manual trigger endpoint to test
POST /api/v1/discovery-schedules/schedules/{id}/run
```

### Frontend Build Errors

**Symptom:** TypeScript errors or build failures

**Solution:**
```powershell
cd d:\MVP\frontend

# Clean install
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json
npm install

# Clear cache
npm run dev -- --force
```

### API 404 Errors

**Check Router Registration:**
```python
# In backend/app/api/v1/__init__.py
from app.api.v1 import discovery_schedules
api_router.include_router(discovery_schedules.router)
```

**Verify OpenAPI Docs:**
Visit `http://localhost:8000/docs` and check if `/api/v1/discovery-schedules/*` endpoints are listed.

### Database Hangs

**Symptom:** Queries timeout, connections pile up

**Solution:**
```powershell
# Restart PostgreSQL
docker compose -f docker-compose.test.yml restart postgres

# Restart backend
# Stop backend (Ctrl+C)
python main.py

# Check connection pool settings in database.py
```

---

## 🏗️ Architecture Details

### Data Flow

```
User Creates Schedule → Database
                      ↓
Celery Beat checks every 5 mins
                      ↓
Finds schedules where next_run_at <= now
                      ↓
Celery Worker executes discovery
                      ↓
Apify/Scrapling fetches leads
                      ↓
For each lead: LeadService.create_or_update_lead()
                      ↓
NEW_LEAD event fired
                      ↓
WorkflowEngine picks up event
                      ↓
Auto-qualification workflow runs
                      ↓
Lead scored → CRM sync → Outreach queued
```

### Database Schema

**discovery_schedules**
```sql
- id: UUID (PK)
- name: VARCHAR (unique)
- description: TEXT
- is_active: BOOLEAN
- schedule_type: ENUM (HOURLY, DAILY, WEEKLY, CUSTOM)
- cron_expression: VARCHAR
- interval_hours: INTEGER
- max_leads_per_run: INTEGER
- last_run_at: TIMESTAMP
- next_run_at: TIMESTAMP
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

**discovery_targets**
```sql
- id: UUID (PK)
- schedule_id: UUID (FK → discovery_schedules)
- target_type: ENUM (CITY, STATE, COUNTRY, INDUSTRY, CATEGORY)
- target_value: VARCHAR
- priority: INTEGER
- created_at: TIMESTAMP
```

**discovery_runs**
```sql
- id: UUID (PK)
- schedule_id: UUID (FK → discovery_schedules)
- status: ENUM (RUNNING, COMPLETED, FAILED)
- started_at: TIMESTAMP
- completed_at: TIMESTAMP
- leads_discovered: INTEGER
- leads_created: INTEGER
- error_message: TEXT
- target_snapshot: JSONB
```

### Celery Tasks

**1. execute_scheduled_discovery_task**
- **Trigger:** Celery beat every 5 minutes
- **Purpose:** Find and execute due schedules
- **Logic:**
  ```python
  1. Query schedules where next_run_at <= now AND is_active = true
  2. For each schedule:
     - Create DiscoveryRun record
     - Fetch targets
     - Call discovery provider (Apify/Scrapling)
     - Create leads
     - Fire NEW_LEAD events
     - Update run status
     - Calculate next_run_at
  ```

**2. cleanup_old_discovery_runs_task**
- **Trigger:** Daily at 2 AM
- **Purpose:** Archive or delete runs older than 90 days
- **Logic:**
  ```python
  DELETE FROM discovery_runs 
  WHERE created_at < (NOW() - INTERVAL '90 days')
  ```

**3. monitor_scheduled_discoveries_task**
- **Trigger:** Every 30 minutes
- **Purpose:** Alert on stuck/failed runs
- **Logic:**
  ```python
  1. Find runs with status=RUNNING and started_at > 1 hour ago
  2. Send alerts
  3. Mark as FAILED with timeout error
  ```

### Event System

**Event Bus:** `app/core/event_bus.py`

**Event Types:**
```python
class EventType(str, Enum):
    NEW_LEAD = "NEW_LEAD"
    UNSUBSCRIBE = "UNSUBSCRIBE"
    REPLY_CLASSIFIED = "REPLY_CLASSIFIED"
```

**Wiring Locations:**
1. **NEW_LEAD** → `app/services/lead_service.py:create_or_update_lead()`
2. **UNSUBSCRIBE** → `app/services/outreach_service.py:add_to_suppression()`
3. **REPLY_CLASSIFIED** → `app/services/reply_intelligence_service.py:process_incoming_message()`

**Workflow Actions:**
```python
# Example: Auto-qualify new leads
@event_handler(EventType.NEW_LEAD)
async def auto_qualify_lead(event_data):
    lead_id = event_data['lead_id']
    
    # Score lead
    score = await scoring_service.calculate_score(lead_id)
    
    # Update CRM
    await crm_service.sync_lead(lead_id)
    
    # Queue outreach if high score
    if score >= 70:
        await outreach_service.queue_campaign(lead_id)
```

---

## 📚 Additional Resources

### Documentation Files
- `backend/SCHEDULED_DISCOVERY_GUIDE.md` - Detailed service usage
- `backend/test_discovery_schedule.py` - Test examples and patterns
- `INTEGRATION_VERIFICATION.md` - Integration test results

### UI Pages
- **Discovery Scheduler:** `http://localhost:5174/discovery-scheduler`
- **Workflow Monitor:** `http://localhost:5174/workflow-monitor`
- **API Documentation:** `http://localhost:8000/docs`

### Code References
- **Backend Models:** `backend/app/models/discovery_schedule.py`
- **Backend Service:** `backend/app/services/discovery_schedule_service.py`
- **Backend API:** `backend/app/api/v1/discovery_schedules.py`
- **Celery Tasks:** `backend/app/workers/scheduled_discovery.py`
- **Frontend Hooks:** `frontend/src/hooks/useDiscoverySchedules.ts`
- **Frontend UI:** `frontend/src/pages/DiscoveryScheduler.tsx`

---

## 🎉 Success Checklist

Use this to verify your setup is complete:

- [ ] PostgreSQL container running (port 5432)
- [ ] Redis container running (port 6379)
- [ ] pgvector extension enabled
- [ ] Backend API running (port 8000)
- [ ] Frontend dev server running (port 5173/5174)
- [ ] Celery worker running
- [ ] Celery beat scheduler running
- [ ] Can access `/docs` endpoint
- [ ] Can access frontend at root URL
- [ ] Can create schedule via API
- [ ] Schedule persists in database
- [ ] Manual run trigger works
- [ ] NEW_LEAD events fire when leads created

**All checked?** Your automated discovery system is fully operational! 🚀

---

**Last Updated:** November 10, 2026  
**Workflow:** wf_272ec758668da4f8  
**Version:** 1.0.0
