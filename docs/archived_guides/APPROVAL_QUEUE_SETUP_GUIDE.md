# 📧 Approval Queue Setup - Step-by-Step Guide

**Complete guide to populate and test the approval queue**

---

## 🎯 Why Is Queue Empty?

**Current Message:** "No items in queue with status 'PENDING'"

**Reasons:**
1. No leads have "Draft Outreach" clicked
2. No sequences enrolled yet
3. No workflows generated outreach
4. Fresh installation (no test data)

**This is NORMAL for new setup!**

---

## 📝 3 Ways to Create Draft Emails

### Method 1: Manual "Draft Outreach" (Easiest)

**Step-by-Step:**

#### 1. Create or Find a Lead

**Option A: Use Existing Lead**
```
1. Go to: http://localhost:5173/leads
2. Find any lead in the list
3. Click on lead name to open details
```

**Option B: Create Test Lead**
```
1. Go to: http://localhost:5173/leads
2. Click: "+ New Lead" button
3. Fill form:
   - Company Name: "Test Restaurant Mumbai"
   - Email: "test@testcompany.com"  (use your own email for testing)
   - Phone: "+91-9876543210"
   - Industry: "Restaurant"
   - Status: "Qualified"
4. Click: "Save Lead"
```

#### 2. Open Lead Details Page

```
1. Click on the lead you just created
2. Lead detail page opens
3. Look for: "Actions" or "Outreach" section
```

#### 3. Click "Draft Outreach" Button

```
1. Find button labeled: "Draft Outreach" or "Generate Email"
2. Click it
3. System will:
   ├─ Analyze lead data
   ├─ Generate personalized email using AI
   ├─ Create draft in approval queue
   └─ Show success message
```

#### 4. Check Approval Queue

```
1. Go to: http://localhost:5173/outreach
2. Click: "Approval Queue" tab
3. Status: "PENDING"
4. You should see: 1 draft email
```

**What You'll See:**
```
┌─────────────────────────────────────────────┐
│ PENDING (1)                                 │
├─────────────────────────────────────────────┤
│ To: test@testcompany.com                    │
│ Subject: Quick question regarding...        │
│ Preview: Hi [Name], I noticed...           │
│                                             │
│ [Approve] [Edit] [Reject]                  │
└─────────────────────────────────────────────┘
```

---

### Method 2: Enroll in Sequence (Automated)

**Step-by-Step:**

#### 1. Go to Sequences Page

```
URL: http://localhost:5173/sequences
or
Navigation: Dashboard → Outreach → Sequences
```

#### 2. Find B2B_PROSPECTING Sequence

```
Look for:
┌─────────────────────────────────────────────┐
│ B2B_PROSPECTING                             │
│ Standard 4-Touch B2B Prospecting Cadence    │
│ Steps: 4 | Active: Yes                      │
│ [View] [Add Leads]                          │
└─────────────────────────────────────────────┘
```

#### 3. Click "Add Leads" or "Enroll Leads"

```
1. Click: "Add Leads" button
2. Modal opens: "Enroll Leads in Sequence"
3. Search or select leads:
   ☐ Test Restaurant Mumbai (test@testcompany.com)
   ☐ Another Lead
4. Click: "Enroll Selected"
```

#### 4. System Creates 4 Draft Emails

```
Sequence has 4 steps:
├─ Step 1 (Day 0):  Intro email
├─ Step 2 (Day 3):  Value prop
├─ Step 3 (Day 7):  Case study
└─ Step 4 (Day 14): Breakup

Each step → 1 draft email in approval queue

Total: 4 PENDING emails
```

#### 5. Check Approval Queue

```
Go to: http://localhost:5173/outreach → Approval Queue

You should see:
┌─────────────────────────────────────────────┐
│ PENDING (4)                                 │
├─────────────────────────────────────────────┤
│ 1. Day 0:  Quick question regarding...     │
│ 2. Day 3:  Idea for reducing...            │
│ 3. Day 7:  How similar businesses...       │
│ 4. Day 14: Closing the loop...             │
└─────────────────────────────────────────────┘
```

---

### Method 3: Trigger via NEW_LEAD Event (Fully Automated)

**Step-by-Step:**

#### 1. Create Discovery Schedule

```
1. Go to: http://localhost:5173/discovery-scheduler
2. Click: "+ Create Schedule"
3. Fill form:
   - Name: "Test Discovery"
   - Schedule Type: "DAILY"
   - Max Leads: 10
   - Target: CITY → "Mumbai"
   - Target: CATEGORY → "Restaurant"
4. Click: "Save Schedule"
```

#### 2. Trigger Manual Discovery Run

```
1. Find your schedule in list
2. Click: "Run Now" button
3. Wait: 30-60 seconds for completion
4. Check: Discovery runs table for status
```

#### 3. NEW_LEAD Event Fires

```
When leads are discovered:
├─ LeadService.create_or_update_lead()
├─ NEW_LEAD event emitted
├─ Auto-Qualify workflow triggered
└─ Workflow generates outreach draft
```

#### 4. Check Approval Queue

```
Go to: Outreach → Approval Queue

Should see:
├─ Leads discovered from Mumbai
├─ Each lead = 1 draft email
└─ Status: PENDING
```

---

## 🧪 Quick Test (5 Minutes)

### Fastest Way to Test Right Now

**Method: Manual API Call**

#### Step 1: Create Test Lead via API

```powershell
$headers = @{
    "X-API-Key" = "test-api-key-2025"
    "Content-Type" = "application/json"
}

$body = @{
    company_name = "Test Restaurant ABC"
    email = "your-email@gmail.com"  # USE YOUR REAL EMAIL
    phone = "+91-9876543210"
    industry = "Restaurant"
    city = "Mumbai"
    status = "qualified"
    source = "manual_test"
} | ConvertTo-Json

$lead = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads" `
    -Method POST -Headers $headers -Body $body

Write-Host "Lead Created: $($lead.id)"
```

#### Step 2: Generate Outreach Draft via API

```powershell
$leadId = $lead.id

$draftBody = @{
    lead_id = $leadId
    template_type = "cold_intro"
    personalization = @{
        company_name = "Test Restaurant ABC"
        industry = "Restaurant"
        city = "Mumbai"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/outreach/drafts" `
    -Method POST -Headers $headers -Body $draftBody

Write-Host "Draft Created!"
```

#### Step 3: Check Approval Queue

```powershell
# List pending approvals
$queue = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/outreach/queue?status=PENDING" `
    -Headers $headers

Write-Host "Pending Emails: $($queue.Count)"
$queue | ForEach-Object {
    Write-Host "  • To: $($_.recipient_email)"
    Write-Host "    Subject: $($_.subject)"
}
```

#### Step 4: Open UI to Approve

```
1. Browser: http://localhost:5173/outreach
2. Tab: Approval Queue
3. Status: PENDING (1)
4. Click: "Approve" button
5. Email will be queued for sending!
```

---

## 📊 Database Verification

### Check if Drafts Exist in Database

```powershell
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c "
SELECT 
  id,
  recipient_email,
  subject,
  status,
  created_at
FROM outreach_queue
WHERE status = 'PENDING_APPROVAL'
ORDER BY created_at DESC
LIMIT 10;
"
```

**If Empty:**
```
No rows returned = No drafts created yet
```

**If Rows Exist:**
```
 id | recipient_email | subject | status | created_at
----+-----------------+---------+--------+------------
...
```

### Check Lead Count

```powershell
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c "
SELECT COUNT(*) as total_leads FROM business_leads;
"
```

### Check Sequence Enrollments

```powershell
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c "
SELECT 
  COUNT(*) as enrolled_leads
FROM sequence_enrollments
WHERE status = 'ACTIVE';
"
```

---

## 🔧 Troubleshooting

### Problem 1: "Draft Outreach" Button Not Found

**Solution:**
1. Check lead status = "Qualified" (only qualified leads get outreach)
2. Look for button in:
   - Lead detail page → Actions section
   - Lead list → Actions dropdown
   - Toolbar → Bulk actions

**Alternative:**
Use API method (see Quick Test above)

---

### Problem 2: Button Clicked But Nothing in Queue

**Possible Causes:**

**A. JavaScript Error**
```
1. Open browser console (F12)
2. Look for errors (red text)
3. Common issues:
   - API endpoint not found (404)
   - Authentication failed (401)
   - CORS error
```

**B. API Not Configured**
```
Check backend logs (Terminal 12):
Look for: POST /api/v1/outreach/drafts
Status should be: 201 Created
```

**C. Database Insert Failed**
```
Check backend logs for:
- SQL errors
- Constraint violations
- Missing required fields
```

**Debug Steps:**
```powershell
# 1. Check backend is running
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" `
    -Headers @{"X-API-Key"="test-api-key-2025"}

# 2. Check outreach API exists
Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing | 
    Select-String "outreach"

# 3. Manual API test
# (See Quick Test section above)
```

---

### Problem 3: Emails Created But Not Visible in UI

**Check Frontend API Call:**
```
Browser Console (F12) → Network tab:
1. Go to: Approval Queue page
2. Look for: GET /api/v1/outreach/queue?status=PENDING
3. Check response:
   - Status: 200 OK
   - Body: Array of drafts
   - If empty array = Database has no drafts
```

**Check Filter:**
```
UI might be filtering by:
- Status (PENDING selected?)
- Date range
- Recipient
- Campaign

Try: Click "ALL" tab to see all statuses
```

---

## 🎯 Complete Test Scenario

### End-to-End Test (15 Minutes)

#### Phase 1: Setup (5 mins)

```
1. ✅ Backend running (port 8000)
2. ✅ Frontend running (port 5173)
3. ✅ Database accessible
4. ✅ Browser open
```

#### Phase 2: Create Test Lead (2 mins)

```
Method: UI or API (choose one)

Option A: Via UI
1. http://localhost:5173/leads
2. Click "+ New Lead"
3. Fill form with YOUR email
4. Save

Option B: Via API
1. Run PowerShell command from "Quick Test" section
2. Note the lead_id returned
```

#### Phase 3: Generate Draft (1 min)

```
Method: UI or API

Option A: Via UI
1. Open lead details
2. Click "Draft Outreach"
3. Wait for success message

Option B: Via API
1. Run draft generation command
2. Check response status = 201
```

#### Phase 4: Verify in Queue (1 min)

```
1. Go to: http://localhost:5173/outreach
2. Tab: Approval Queue
3. Status: PENDING
4. Should see: 1 email draft

If NOT visible:
- Click "Refresh" button
- Try "ALL" tab
- Check database directly
```

#### Phase 5: Review & Approve (3 mins)

```
1. Click on draft to expand
2. Review:
   ✓ Recipient email correct
   ✓ Subject makes sense
   ✓ Body personalized ({{variables}} filled)
   ✓ No typos/errors
3. Actions:
   - Approve → Email queued for sending
   - Edit → Modify and re-submit
   - Reject → Discard draft
```

#### Phase 6: Verify Approval (2 mins)

```
After clicking "Approve":

1. Draft should move to "SENT" tab
2. Check backend logs for:
   - Email queued message
   - Scheduled send time
3. Database check:
   UPDATE outreach_queue 
   SET status = 'APPROVED'
   WHERE id = 'draft-id'
```

#### Phase 7: Check Email Delivery (1 min)

```
Wait 2-5 minutes, then:

1. Check your email inbox
2. Look for email from system
3. Verify:
   ✓ Subject correct
   ✓ Content personalized
   ✓ No {{variables}} remaining
   ✓ Links work

Note: In dev mode, emails might go to:
- Local SMTP catcher
- SendGrid test mode
- Print to console only
```

---

## 📋 Checklist: Is System Ready?

### Pre-Flight Checks

```
Environment:
☐ Backend running (http://localhost:8000/api/v1/health returns 200)
☐ Frontend running (http://localhost:5173 loads)
☐ Database connected (can query tables)
☐ Redis running (Celery worker active)

Configuration:
☐ Email templates exist in database
☐ SMTP settings configured (or test mode)
☐ API keys valid
☐ Workflow definitions active

Data:
☐ At least 1 qualified lead exists
☐ Lead has valid email address
☐ Lead not in suppression list

Permissions:
☐ User has permission to draft outreach
☐ Campaign/sequence is active
☐ No global kill switch enabled
```

### Post-Creation Checks

```
After creating draft:
☐ Database has row in outreach_queue
☐ Status = 'PENDING_APPROVAL'
☐ UI shows draft in queue
☐ Can open and read full content
☐ Approve/Reject buttons work
```

---

## 🚀 Next Steps After First Draft

### 1. Bulk Enrollment

```
Once you verify one draft works:

1. Create multiple leads (10-20)
2. Enroll all in B2B_PROSPECTING sequence
3. Result: 40-80 drafts (4 per lead)
4. Practice bulk review/approval workflow
```

### 2. Customize Templates

```
1. Database: email_templates table
2. Edit templates for your business
3. Test personalization {{variables}}
4. Verify AI-generated content quality
```

### 3. Configure Sending Schedule

```
1. Set optimal send times
2. Respect business hours
3. Add delays between batches
4. Monitor deliverability
```

### 4. Monitor & Optimize

```
Track:
- Approval rate (how many you approve vs reject)
- Send success rate
- Open rates
- Reply rates

Optimize:
- Template content
- Subject lines
- Send timing
- Target audience
```

---

## 📚 API Reference

### Create Draft Email

```
POST /api/v1/outreach/drafts

Headers:
  X-API-Key: test-api-key-2025
  Content-Type: application/json

Body:
{
  "lead_id": "uuid",
  "template_type": "cold_intro",
  "personalization": {
    "company_name": "Example Corp",
    "industry": "Technology"
  }
}

Response: 201 Created
{
  "id": "draft-uuid",
  "status": "PENDING_APPROVAL",
  "subject": "Quick question...",
  "scheduled_for": "2026-11-13T15:00:00Z"
}
```

### List Approval Queue

```
GET /api/v1/outreach/queue?status=PENDING

Response: 200 OK
[
  {
    "id": "draft-uuid",
    "recipient_email": "test@example.com",
    "subject": "Quick question...",
    "body": "Hi John,...",
    "status": "PENDING_APPROVAL",
    "created_at": "2026-11-12T14:00:00Z"
  }
]
```

### Approve Draft

```
POST /api/v1/outreach/queue/{draft_id}/approve

Response: 200 OK
{
  "id": "draft-uuid",
  "status": "APPROVED",
  "approved_by": "user-id",
  "approved_at": "2026-11-12T14:30:00Z",
  "scheduled_for": "2026-11-12T15:00:00Z"
}
```

### Reject Draft

```
POST /api/v1/outreach/queue/{draft_id}/reject

Body:
{
  "reason": "Content not relevant"
}

Response: 200 OK
{
  "id": "draft-uuid",
  "status": "REJECTED",
  "rejected_at": "2026-11-12T14:30:00Z"
}
```

---

## 🎉 Summary

### To Get Drafts in Approval Queue:

**Fastest Method (2 minutes):**
```
1. Use PowerShell API calls from "Quick Test" section
2. Create lead → Generate draft → Check queue
```

**UI Method (5 minutes):**
```
1. Create test lead in UI
2. Click "Draft Outreach" on lead
3. Go to Approval Queue
4. Review and approve
```

**Automated Method (10 minutes):**
```
1. Create discovery schedule
2. Run discovery (finds leads)
3. NEW_LEAD workflow triggers
4. Drafts auto-generated
5. Check approval queue
```

### Why Queue Was Empty:

- ✅ System working correctly
- ⚠️ No drafts created yet (expected for fresh install)
- 🎯 Just need to trigger draft creation

### Action Plan:

1. Pick one method above
2. Create test draft
3. Verify in queue
4. Approve it
5. Monitor sending
6. Scale up!

---

**Ready to test? Let me know which method you want to try first!** 🚀

**Detailed Guide:** `d:\MVP\APPROVAL_QUEUE_SETUP_GUIDE.md`
