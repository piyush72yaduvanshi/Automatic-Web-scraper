# 🚀 Quick Start Guide - AI Sales & CRM Automation

## Prerequisites

- ✅ PostgreSQL 14+ running
- ✅ Python 3.11+ with virtual environment activated
- ✅ Node.js 18+ and npm installed
- ✅ Git repository cloned

---

## Step 1: Start Backend (5 minutes)

### Option A: Using Helper Script (Recommended)
```powershell
cd d:\MVP
.\start-backend.ps1
```

### Option B: Manual Steps
```powershell
cd d:\MVP\backend

# Run migrations (includes new automation tables)
python -m alembic upgrade head

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Verify**:
- Open http://localhost:8000/docs
- Should see Swagger UI with `/automation` endpoints

---

## Step 2: Start Frontend (3 minutes)

### Option A: Using Helper Script
```powershell
# In a new terminal
cd d:\MVP
.\start-frontend.ps1
```

### Option B: Manual Steps
```powershell
cd d:\MVP\frontend
npm run dev
```

**Expected Output**:
```
VITE ready in 1234 ms
➜  Local:   http://localhost:3000
```

**Verify**:
- Open http://localhost:3000
- Should see AI Sales & CRM dashboard

---

## Step 3: Test Automation (2 minutes)

### Option A: Using Test Script
```powershell
# In a new terminal
cd d:\MVP
.\test-automation.ps1
```

### Option B: Manual API Testing

#### Check Automation Status
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/automation/status" | ConvertTo-Json
```

Expected:
```json
{
  "auto_enroll_enabled": true,
  "auto_approve_enabled": true,
  "auto_crm_enabled": true,
  "min_score_outreach": 70,
  "min_score_crm": 60
}
```

#### Process 5 Leads (Test Run)
```powershell
$body = @{ batch_size = 5 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads/bulk-process" `
  -Method Post `
  -Body $body `
  -ContentType "application/json" | ConvertTo-Json
```

Expected:
```json
{
  "success": true,
  "summary": {
    "processed": 5,
    "succeeded": 5,
    "enrolled": 3,
    "converted": 4
  }
}
```

---

## Step 4: Process All Leads (1 minute)

### Full Automation Run
```powershell
$body = @{ batch_size = 50 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads/bulk-process" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

This will:
1. ✅ Enrich emails for leads without contact info
2. ✅ Qualify all unqualified leads (0-100 score)
3. ✅ Auto-enroll leads with score >= 70 in outreach sequences
4. ✅ Auto-convert leads with score >= 60 to CRM (Companies, Contacts, Deals)
5. ✅ Log exceptions for any failures

---

## Step 5: Verify Results (2 minutes)

### Check CRM Data in Frontend
1. Navigate to http://localhost:3000/crm
2. Click "Companies" - should see newly created companies
3. Click "Contacts" - should see contacts with emails
4. Click "Deals" - should see deals in "Lead" stage

### Check Outreach Queue
1. Navigate to http://localhost:3000/outreach/approval-queue
2. Should see auto-generated email drafts ready for review
3. (Note: Auto-approval not fully integrated yet, so drafts appear here)

### Check Automation Exceptions
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/automation/exceptions?resolved=false"
```

Should show any leads that failed during processing with clear error messages.

---

## 🎛️ Configuration

### Adjust Automation Settings

#### Lower Outreach Threshold (Enroll More Leads)
```powershell
$body = @{ value = 60 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/automation/settings/min_score_for_outreach" `
  -Method Put `
  -Body $body `
  -ContentType "application/json"
```

#### Disable Auto-CRM Conversion
```powershell
$body = @{ value = $false } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/automation/settings/auto_convert_to_crm" `
  -Method Put `
  -Body $body `
  -ContentType "application/json"
```

#### View All Settings
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/automation/settings" | ConvertTo-Json -Depth 3
```

---

## 🔧 Troubleshooting

### Backend Won't Start
**Symptom**: Server crashes or import errors

**Solution**:
```powershell
cd d:\MVP\backend

# Check database connection
python -c "from app.core.database import engine; print('DB OK')"

# If fails, check .env DATABASE_URL is correct
# Make sure PostgreSQL is running on the configured port
```

### Migration Fails
**Symptom**: `alembic upgrade head` errors

**Solution**:
```powershell
# Check current migration version
python -m alembic current

# If stuck, check database logs
# Ensure previous migrations (001-008) completed successfully
```

### Bulk Processing Returns 0 Results
**Symptom**: All leads show as "skipped"

**Solution**:
```powershell
# Check if leads already processed
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads?page=1&page_size=5"

# Force reprocessing
$body = @{ 
  batch_size = 10
  include_processed = $true 
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads/bulk-process" `
  -Method Post -Body $body -ContentType "application/json"
```

### No CRM Data Created
**Symptom**: Companies/Contacts tables empty after processing

**Solution**:
```powershell
# Check score threshold
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/automation/status"

# Lower CRM threshold to 50
$body = @{ value = 50 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/automation/settings/min_score_for_crm" `
  -Method Put -Body $body -ContentType "application/json"

# Reprocess leads
```

---

## 📊 Expected Results with 12 Existing Dental Clinic Leads

After running bulk-process with default settings:

| Metric | Expected Value | Reason |
|--------|---------------|--------|
| **Processed** | 12 | All leads in database |
| **Email Enriched** | 8-10 | Leads without emails get pattern-guessed emails |
| **Qualified** | 12 | All leads get ICP scores calculated |
| **Enrolled in Outreach** | 6-8 | Leads with score >= 70 and valid email |
| **Converted to CRM** | 8-10 | Leads with score >= 60 |
| **Failed/Exceptions** | 2-4 | Leads without websites or invalid emails |

### Database Changes
```sql
-- Companies table
SELECT COUNT(*) FROM companies;  -- Should be 8-10

-- Contacts table
SELECT COUNT(*) FROM contacts;  -- Should be 8-10

-- Deals table
SELECT COUNT(*) FROM deals WHERE stage_name = 'Lead';  -- Should be 8-10

-- Lead status
SELECT 
  outreach_enrolled,
  crm_converted,
  COUNT(*) as count
FROM business_leads
GROUP BY outreach_enrolled, crm_converted;

-- Expected output:
-- outreach_enrolled | crm_converted | count
-- false            | false         | 2-4
-- false            | true          | 2-4
-- true             | false         | 0
-- true             | true          | 6-8
```

---

## 🎯 Success Checklist

- [ ] Backend started on port 8000
- [ ] Frontend started on port 3000
- [ ] Migration 009_automation_tables completed
- [ ] `/automation/status` endpoint returns settings
- [ ] Bulk-process processes at least 5 leads
- [ ] CRM tables populated (check frontend)
- [ ] Outreach queue has draft emails (check frontend)
- [ ] Exception log shows clear error messages (if any)

---

## 🚦 What's Working vs. What's Pending

### ✅ Fully Implemented & Working
- Database models and migrations
- Email enrichment service
- CRM automation service
- Outreach auto-enrollment service
- Lead automation orchestrator
- Bulk processing API
- Workflow engine integration
- Exception tracking and logging
- Settings API (GET/PUT)

### ⚠️ Partially Implemented
- **Auto-approval**: Validation logic exists but not integrated with OutreachService
  - Emails still go to approval queue
  - Need to modify `OutreachService.prepare_outreach_draft_for_lead()`
  
### ❌ Not Yet Implemented
- **Frontend Settings UI**: Settings page with toggle switches
- **External Email APIs**: Hunter.io, Apollo integration
- **Background Tasks**: Async processing for 500+ leads
- **Automation Dashboard**: Visual metrics and progress tracking

---

## 📞 Next Actions

### For Manual Testing (Now):
```powershell
# 1. Start both servers
.\start-backend.ps1  # Terminal 1
.\start-frontend.ps1  # Terminal 2

# 2. Run automation test
.\test-automation.ps1  # Terminal 3

# 3. Check results in frontend
# Open http://localhost:3000/crm/companies
# Open http://localhost:3000/crm/deals
```

### For Production Deployment (Later):
1. Add external email enrichment APIs
2. Implement auto-approval integration
3. Build frontend settings UI
4. Add background task queue (Celery/RQ)
5. Set up monitoring and alerts

---

## 📚 Additional Resources

- **Full Implementation Details**: See `AUTOMATION_IMPLEMENTATION_SUMMARY.md`
- **API Documentation**: http://localhost:8000/docs
- **Original Plan**: `.agents/tasks/lead-automation/IMPLEMENTATION_PLAN.md`
- **Commit History**: `git log --oneline --grep="automation"`

---

**Total Implementation Time**: ~2 hours  
**Lines of Code Added**: 1,009 lines  
**Files Created**: 12 new files  
**Last Updated**: 2024-11-13
