# 🎯 CRM & Pipeline Module - Complete Analysis

**Status**: ✅ Operational | **Date**: November 12, 2026

---

## 📊 Quick Summary

| Sub-Module | Tables | Data Status | Functionality |
|-----------|--------|-------------|--------------|
| **Business Leads** | 1 table | ✅ 12 leads | Discovery-generated |
| **Companies** | 1 table | ⚠️ Empty | Ready for creation |
| **Contacts** | 1 table | ⚠️ Empty | Ready for creation |
| **Deals Pipeline** | 2 tables | ⚠️ 1 pipeline, 0 deals | Infrastructure ready |
| **Meetings & Calls** | 1 table | ⚠️ Empty | Scheduling ready |
| **Activities** | 1 table | ✅ 5 activities | System events logged |

---

## 🎨 1. Business Leads Module

### Purpose
Discovery aur outreach se aaye hue raw leads ko track karo. Ye CRM ka entry point hai - leads qualify hone ke baad Companies aur Contacts ban jate hain.

### **business_leads** (12 leads - All from Discovery)

**Current Data:**
```yaml
Total Leads: 12
Category: Dental clinics in Lucknow
Source: DISCOVERY (SerpAPI scraping)
Status: enriched
Location: All in Lucknow, Uttar Pradesh

Lead Quality Distribution:
  - qualification_score 71 (Maybe): 2 leads
  - qualification_score 50 (New): 10 leads
  
Top Leads:
  1. Mahima Dental Clinic - Score 71 (Maybe)
     Website: https://mahimadental.co.in/
     
  2. Pushpa Dental Speciality Centre - Score 71 (Maybe)
     Website: https://pushpadental.co.in/
     
  3-12. Various dental clinics - Score 50 (New)
```

**Schema Structure:**
```yaml
Core Info:
  - business_name: Lead ka naam
  - category: Industry/type (e.g., "Dental clinic")
  - website: Website URL
  
Location:
  - address: Full address
  - city, state, country: Geographic data
  
Discovery Data:
  - source_provider: "serpapi" (Google Maps scraping)
  - provider_external_id: External reference
  - lead_source: "DISCOVERY"
  
Qualification:
  - qualification_score: 0-100 (AI scoring)
  - qualification_status: "New" / "Maybe" / "Qualified" / "Disqualified"
  - qualification_reasoning: AI explanation
  - qualification_breakdown: Detailed scoring
  - company_research: Enrichment data
  
Social Engagement:
  - social_engagement_count: Interactions count
  - last_social_engagement_at: Last interaction time
  
Status:
  - status: "enriched" / "qualified" / "converted"
  - company_id: Link to companies table (when converted)
  
Metadata:
  - data_confidence_score: Data quality metric
  - created_at, updated_at: Timestamps
```

---

## 🏢 2. Companies Module

### Purpose
Qualified leads ko full-fledged company records mein convert karo. Multiple contacts ek company se link hote hain.

### **companies** (0 records - Ready for data)

**Schema Structure:**
```yaml
Basic Info:
  - name: Company name
  - domain: Primary domain
  - website: Website URL
  - industry: Industry classification
  - size_range: Employee count ("1-10", "11-50", "51-200", etc.)
  
Location:
  - location: Full address/city
  
Details:
  - description: Company description
  - tech_stack: Technologies used (JSON)
  - annual_revenue: Revenue range
  
Status:
  - status: "ACTIVE" / "INACTIVE" / "PROSPECT"
  - lead_id: Original lead reference (if converted from lead)
  
Timestamps:
  - created_at, updated_at
```

**Workflow: Lead → Company Conversion**
```
1. business_leads mein lead qualify ho jaye (score > 70)
2. Manual review ya workflow trigger
3. Create company record from lead data
4. Link: company.lead_id = lead.id
5. Update: lead.company_id = company.id
6. Lead status = "converted"
```

---

## 👥 3. Contacts Module

### Purpose
Company ke andar individual decision makers aur stakeholders ko track karo. Email outreach, calls, meetings - sab contacts se link hote hain.

### **contacts** (0 records - Ready for data)

**Schema Structure:**
```yaml
Personal Info:
  - first_name, last_name: Contact name
  - email: Primary email
  - phone: Phone number
  - job_title: Position (e.g., "CEO", "Director")
  - department: Department (Sales, Marketing, IT)
  
Professional:
  - linkedin_url: LinkedIn profile
  - is_decision_maker: Boolean (true for C-level, owners)
  
Reachability:
  - reachability_status: "VALID" / "BOUNCED" / "INVALID" / "UNKNOWN"
  
Relationships:
  - company_id: Which company they work for
  - lead_id: Original lead (if applicable)
  
Timestamps:
  - created_at, updated_at
```

**Typical Contact Creation Flow:**
```
1. Company create ho jaye
2. Research: Find decision makers (LinkedIn, company website)
3. Create contact linked to company_id
4. Verify email reachability (email validation API)
5. Mark is_decision_maker = true for key people
6. Use in outreach sequences
```

---

## 💰 4. Deals & Pipeline Module

### Purpose
Sales opportunities ko structured pipeline mein track karo. Qualification se closing tak ka journey.

### **pipelines** (1 default pipeline)

**Current Data:**
```yaml
Pipeline: "Default Sales Pipeline"
ID: e7846364-8c19-4928-bea2-ac966df129af
is_default: true
Created: Nov 10, 2026 12:43 PM
```

**Schema:**
```yaml
- name: Pipeline name
- is_default: Boolean (true for default pipeline)
- created_at: Timestamp
```

**⚠️ Missing: deal_stages table**
```
Pipeline stages normally stored in separate table:
  - Stage 1: Lead
  - Stage 2: Qualified
  - Stage 3: Demo Scheduled
  - Stage 4: Proposal Sent
  - Stage 5: Negotiation
  - Stage 6: Won/Lost

Currently: stage_id in deals table references missing stages.
Solution: Create deal_stages table or hardcode stages.
```

### **deals** (0 records - Ready for opportunities)

**Schema Structure:**
```yaml
Deal Info:
  - title: Deal name ("Q4 2026 - Mahima Dental")
  - amount: Deal value
  - currency: "USD", "INR", etc.
  
Relationships:
  - company_id: Which company
  - contact_id: Primary contact
  - pipeline_id: Which pipeline
  - stage_id: Current stage (references missing deal_stages)
  
Status:
  - status: "OPEN" / "WON" / "LOST"
  - probability: Win probability (0.0 to 1.0)
  - expected_close_date: Target close date
  - lost_reason: Why deal was lost (if applicable)
  
Timestamps:
  - created_at, updated_at
```

**Deal Lifecycle:**
```
1. Qualified lead → Create deal
2. Set initial amount and stage = "Qualified"
3. Move through stages as progress happens
4. Update probability at each stage:
   - Qualified: 20%
   - Demo: 40%
   - Proposal: 60%
   - Negotiation: 80%
5. Final status: WON or LOST
6. If WON: Company status = CUSTOMER
```

---

## 📅 5. Meetings & Calls Module

### Purpose
Discovery calls, demos, negotiations - sabhi meetings ko calendar aur CRM mein sync karo.

### **meetings** (0 records - Ready for scheduling)

**Schema Structure:**
```yaml
Meeting Info:
  - title: Meeting subject
  - start_time, end_time: Schedule
  - agenda: Meeting agenda/purpose
  - meeting_url: Zoom/Meet link
  
Relationships:
  - company_id: Which company
  - contact_id: Attendee(s)
  - deal_id: Related deal (if any)
  
Preparation:
  - prep_notes: Research, talking points
  
Status:
  - status: "SCHEDULED" / "COMPLETED" / "CANCELLED" / "NO_SHOW"
  
Timestamp:
  - created_at: When meeting was created
```

**Meeting Workflow:**
```
1. Contact interested → Schedule discovery call
2. Create meeting record:
   - Link to contact_id and company_id
   - Set agenda (discovery/demo/negotiation)
   - Generate meeting_url (Zoom API integration)
3. Prep: AI generates prep_notes from company_research
4. Day of meeting: Send reminder email
5. Post-meeting: Mark status = COMPLETED
6. Add activity log with meeting notes
7. Update deal stage if applicable
```

---

## 📝 6. Activities (Timeline) Module

### Purpose
Har interaction, event, aur action ko chronological timeline mein log karo. Full audit trail.

### **activities** (5 system activities logged)

**Current Data:**
```yaml
Activity 1: (Nov 12, 2026 14:01)
  Type: SYSTEM
  Title: "Inbound reply received and cataloged"
  Description: "Workflow step executed"
  
Activity 2: (Nov 12, 2026 14:01)
  Type: SYSTEM
  Title: "Contact permanently suppressed upon unsubscribe request"
  Description: "Workflow step executed"
  
Activity 3: (Nov 10, 2026 13:25)
  Type: CALL
  Title: "Sent AUTONOMOUS_WORKFLOW_ACTION to Target Prospects"
  Description: "Subject: Workflow Action: Draft tailored cold email..."
  
Activity 4 & 5: Similar workflow events
```

**Schema Structure:**
```yaml
Activity Type:
  - activity_type: "CALL" / "EMAIL" / "MEETING" / "TASK" / "NOTE" / "SYSTEM"
  
Content:
  - title: Activity headline
  - description: Detailed description
  
Relationships:
  - company_id: Link to company
  - contact_id: Link to contact
  - deal_id: Link to deal
  - lead_id: Link to lead
  
Metadata:
  - activity_metadata: JSON (extra context)
  
Timestamp:
  - created_at: When activity happened
```

**Activity Types Explained:**
```yaml
CALL: Phone calls, discovery calls
  - Log phone number, duration, outcome
  
EMAIL: Sent/received emails
  - Track opens, clicks, replies
  
MEETING: Calendar events
  - Link to meetings table
  
TASK: To-do items
  - Follow-ups, reminders
  
NOTE: Manual notes
  - Sales rep observations
  
SYSTEM: Automated events
  - Workflow executions
  - Status changes
  - Qualification updates
```

---

## 🎯 How CRM & Pipeline Works

### A. Lead-to-Customer Journey

```mermaid
Discovery Scraping (SerpAPI)
       ↓
business_leads (Raw lead - status: enriched)
       ↓
AI Qualification (Score 0-100)
       ↓
qualification_status = "Qualified" (score > 70)
       ↓
Convert to Company + Contact
       ↓
companies table (status: PROSPECT)
contacts table (is_decision_maker: true)
       ↓
Outreach Sequence (Cold email/LinkedIn)
       ↓
Reply received → activities (SYSTEM log)
       ↓
Create Deal (status: OPEN, stage: Qualified)
       ↓
Schedule Discovery Call
       ↓
meetings table (status: SCHEDULED)
       ↓
Meeting completed → Update deal stage
       ↓
Demo given → stage: Demo, probability: 40%
       ↓
Proposal sent → stage: Proposal, probability: 60%
       ↓
Negotiation → stage: Negotiation, probability: 80%
       ↓
Deal WON → status: WON, company.status: CUSTOMER
       ↓
Onboarding begins
```

### B. Daily CRM Operations

**Sales Rep Workflow:**
```
Morning:
1. Check dashboard → See today's tasks
2. Review scheduled meetings → Read prep_notes
3. Follow up on open deals → Update stage/probability

During Day:
4. Log every call → activities table
5. Send emails → Track in activities
6. Meeting happens → Mark completed, add notes
7. Lead replies → Workflow auto-creates activity

Evening:
8. Update deal amounts → Keep forecast accurate
9. Create tasks for tomorrow → Set reminders
10. Add notes to contacts → Document insights
```

**Manager Dashboard:**
```
Pipeline View:
- Total deals by stage
- Win rate percentage
- Average deal size
- Sales velocity (days in stage)

Team Performance:
- Deals won per rep
- Activities per rep (call/email count)
- Meeting completion rate
- Response rate to outreach
```

---

## 🚀 Missing Infrastructure

### Tables That Should Exist (But Don't)

#### 1. **deal_stages**
```sql
CREATE TABLE deal_stages (
    id UUID PRIMARY KEY,
    pipeline_id UUID REFERENCES pipelines(id),
    name VARCHAR(100),          -- "Qualified", "Demo", "Proposal"
    order_index INT,            -- 1, 2, 3 for display order
    probability FLOAT,          -- Default probability (0.2, 0.4, 0.6)
    is_closed_won BOOLEAN,
    is_closed_lost BOOLEAN
);

-- Default stages for "Default Sales Pipeline":
INSERT INTO deal_stages VALUES
('uuid1', 'pipeline_id', 'Lead', 1, 0.1, false, false),
('uuid2', 'pipeline_id', 'Qualified', 2, 0.2, false, false),
('uuid3', 'pipeline_id', 'Demo Scheduled', 3, 0.4, false, false),
('uuid4', 'pipeline_id', 'Proposal Sent', 4, 0.6, false, false),
('uuid5', 'pipeline_id', 'Negotiation', 5, 0.8, false, false),
('uuid6', 'pipeline_id', 'Closed Won', 6, 1.0, true, false),
('uuid7', 'pipeline_id', 'Closed Lost', 7, 0.0, false, true);
```

#### 2. **tasks**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    due_date TIMESTAMP,
    priority VARCHAR(20),       -- "HIGH", "MEDIUM", "LOW"
    status VARCHAR(20),         -- "PENDING", "COMPLETED"
    company_id UUID REFERENCES companies(id),
    contact_id UUID REFERENCES contacts(id),
    deal_id UUID REFERENCES deals(id),
    assigned_to UUID,           -- User/rep assignment
    created_at TIMESTAMP
);
```

#### 3. **call_logs**
```sql
CREATE TABLE call_logs (
    id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id),
    company_id UUID REFERENCES companies(id),
    deal_id UUID REFERENCES deals(id),
    direction VARCHAR(20),      -- "INBOUND", "OUTBOUND"
    duration_seconds INT,
    phone_number VARCHAR(20),
    recording_url VARCHAR(500),
    transcript TEXT,
    outcome VARCHAR(50),        -- "CONNECTED", "VOICEMAIL", "NO_ANSWER"
    notes TEXT,
    created_at TIMESTAMP
);
```

#### 4. **notes**
```sql
CREATE TABLE notes (
    id UUID PRIMARY KEY,
    content TEXT,
    company_id UUID REFERENCES companies(id),
    contact_id UUID REFERENCES contacts(id),
    deal_id UUID REFERENCES deals(id),
    created_by UUID,            -- User who wrote note
    created_at TIMESTAMP
);
```

#### 5. **emails** (Outreach tracking)
```sql
CREATE TABLE emails (
    id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id),
    company_id UUID REFERENCES companies(id),
    deal_id UUID REFERENCES deals(id),
    subject VARCHAR(255),
    body_text TEXT,
    body_html TEXT,
    direction VARCHAR(20),      -- "SENT", "RECEIVED"
    status VARCHAR(50),         -- "SENT", "DELIVERED", "OPENED", "CLICKED", "BOUNCED"
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    sent_at TIMESTAMP,
    created_at TIMESTAMP
);
```

---

## 📊 Current Data Flow

### What's Happening Now ✅

```
Discovery Module → SerpAPI
       ↓
12 dental clinic leads in business_leads
       ↓
AI qualification (scores: 50-71)
       ↓
Workflows triggering on events:
  - NEW_LEAD → Auto-qualify workflow
  - REPLY_CLASSIFIED → Escalate workflow
  - UNSUBSCRIBE → Suppression workflow
       ↓
5 activities logged in timeline
```

### What's NOT Happening Yet ⚠️

```
❌ No companies created from qualified leads
❌ No contacts extracted
❌ No deals opened
❌ No meetings scheduled
❌ No manual sales rep actions
❌ No pipeline progression
```

### Why?
```
Reason 1: Leads need manual review before company conversion
Reason 2: Contact details need enrichment (emails, phone numbers)
Reason 3: No sales rep assigned yet to work these leads
Reason 4: Missing deal_stages table for pipeline functionality
```

---

## 🎬 How to Test CRM Module

### Test 1: Convert Lead to Company
```powershell
# Step 1: Pick a qualified lead
$leadId = "c3807344-6875-44af-b638-bdd9bd9d593d"  # Mahima Dental Clinic (score 71)

# Step 2: Create company from lead
$body = @{
    name = "Mahima Dental Clinic"
    website = "https://mahimadental.co.in/"
    industry = "Healthcare - Dental"
    size_range = "1-10"
    location = "Lucknow, Uttar Pradesh, India"
    status = "PROSPECT"
    lead_id = $leadId
} | ConvertTo-Json

$company = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/companies" `
    -Method POST -ContentType "application/json" -Body $body

$company
```

**Expected Response:**
```json
{
  "id": "new-company-uuid",
  "name": "Mahima Dental Clinic",
  "status": "PROSPECT",
  "lead_id": "c3807344-6875-44af-b638-bdd9bd9d593d"
}
```

### Test 2: Add Contact to Company
```powershell
$companyId = "company-uuid-from-above"

$body = @{
    company_id = $companyId
    first_name = "Dr. Mahima"
    last_name = "Verma"
    email = "contact@mahimadental.co.in"  # Need to find real email
    job_title = "Founder & Chief Dentist"
    department = "Management"
    is_decision_maker = $true
    reachability_status = "UNKNOWN"
} | ConvertTo-Json

$contact = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/contacts" `
    -Method POST -ContentType "application/json" -Body $body

$contact
```

### Test 3: Create Deal for Company
```powershell
$body = @{
    title = "Q4 2026 - Mahima Dental Clinic"
    company_id = $companyId
    contact_id = $contactId
    pipeline_id = "e7846364-8c19-4928-bea2-ac966df129af"  # Default pipeline
    amount = 50000.0
    currency = "INR"
    status = "OPEN"
    probability = 0.2
    expected_close_date = "2026-12-31T00:00:00"
} | ConvertTo-Json

$deal = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/deals" `
    -Method POST -ContentType "application/json" -Body $body

$deal
```

**⚠️ Note:** This will fail if stage_id is required but deal_stages table doesn't exist.

### Test 4: Schedule Meeting
```powershell
$body = @{
    title = "Discovery Call - Mahima Dental"
    company_id = $companyId
    contact_id = $contactId
    deal_id = $dealId
    start_time = (Get-Date).AddDays(2).ToString("yyyy-MM-ddTHH:mm:ss")
    end_time = (Get-Date).AddDays(2).AddMinutes(30).ToString("yyyy-MM-ddTHH:mm:ss")
    agenda = "Discuss current CRM pain points and AI automation opportunities"
    meeting_url = "https://zoom.us/j/123456789"
    status = "SCHEDULED"
    prep_notes = "Dental clinic in Lucknow. Score 71. Website: mahimadental.co.in"
} | ConvertTo-Json

$meeting = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/meetings" `
    -Method POST -ContentType "application/json" -Body $body

$meeting
```

### Test 5: Log Activity
```powershell
$body = @{
    activity_type = "CALL"
    title = "Cold call to Mahima Dental Clinic"
    description = "Spoke with receptionist. Asked to email details to contact@mahimadental.co.in"
    company_id = $companyId
    contact_id = $contactId
    deal_id = $dealId
} | ConvertTo-Json

$activity = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/activities" `
    -Method POST -ContentType "application/json" -Body $body

$activity
```

---

## 📈 Frontend Pages

### Expected CRM Pages

| Page | File | Purpose |
|------|------|---------|
| **Companies** | `Companies.tsx` | List all companies, filter by status |
| **Contacts** | `Contacts.tsx` | List all contacts, filter by company |
| **Deals Pipeline** | `DealsPipeline.tsx` | Kanban view of deals by stage |
| **Leads** | `Leads.tsx` | List business_leads, qualification queue |
| **Meetings** | `MeetingsView.tsx` | Calendar view of scheduled meetings |
| **Tasks** | `TasksMeetings.tsx` | To-do list, follow-ups |

### Navigation Structure
```
CRM & Pipeline
├── Leads (business_leads)
├── Companies (companies)
├── Contacts (contacts)
├── Deals & Pipeline (deals + pipeline visualization)
├── Kanban (drag-drop stage management)
├── Meetings & Calls (meetings + call_logs)
└── Tasks & Follow-ups (tasks)
```

---

## 🎯 Key Insights

### What's Strong ✅
1. **12 real leads** from Discovery module (dental clinics)
2. **Solid data structure** - proper relationships between tables
3. **Activity logging** working - timeline tracking events
4. **Pipeline infrastructure** ready - 1 default pipeline created
5. **Workflow integration** - activities auto-logged on events

### What Needs Work ⚠️
1. **Lead conversion** - No companies/contacts created yet
2. **deal_stages table missing** - Can't properly use pipeline
3. **Contact enrichment** - Need emails, phone numbers for outreach
4. **Sales rep assignment** - No user/rep management yet
5. **Frontend testing** - UI pages need verification

### What's Missing ❌
1. `deal_stages` table - Pipeline stages definition
2. `tasks` table - To-do list functionality
3. `call_logs` table - Phone call tracking
4. `notes` table - Manual note-taking
5. `emails` table - Email tracking (sent/opened/clicked)

---

## 💡 Recommended Next Steps

### Step 1: Create Deal Stages (High Priority)
```sql
-- Run migration to create deal_stages table
-- Add default 7 stages to Default Sales Pipeline
-- Update frontend to show stage progression
```

### Step 2: Convert Top Leads to Companies
```
- Take 2 qualified leads (score 71)
- Create companies manually via API
- Research and add contacts
- Verify email addresses
- Create initial deals
```

### Step 3: Test Full Sales Cycle
```
1. Lead → Company conversion
2. Contact creation + enrichment
3. Deal creation + stage movement
4. Meeting scheduling
5. Activity logging
6. Deal won/lost
```

### Step 4: Frontend Verification
```
- Open each CRM page in browser
- Verify data displays correctly
- Test filtering, sorting, search
- Check Kanban drag-drop
- Verify meeting calendar
```

### Step 5: Missing Tables Implementation
```
- Implement tasks table + API
- Implement call_logs table + API
- Implement notes table + API
- Implement emails table (or integrate with existing)
- Update frontend to use new tables
```

---

## 📚 API Endpoints Reference

### Leads APIs
```
GET    /api/v1/leads                    # List all leads
GET    /api/v1/leads/{id}               # Get lead details
PATCH  /api/v1/leads/{id}/qualify       # Manual qualification
POST   /api/v1/leads/{id}/convert       # Convert to company
```

### Companies APIs
```
GET    /api/v1/companies                # List all companies
POST   /api/v1/companies                # Create company
GET    /api/v1/companies/{id}           # Company details
PATCH  /api/v1/companies/{id}           # Update company
DELETE /api/v1/companies/{id}           # Delete company
```

### Contacts APIs
```
GET    /api/v1/contacts                 # List all contacts
POST   /api/v1/contacts                 # Create contact
GET    /api/v1/contacts/{id}            # Contact details
PATCH  /api/v1/contacts/{id}            # Update contact
POST   /api/v1/contacts/{id}/verify     # Verify email
```

### Deals APIs
```
GET    /api/v1/deals                    # List all deals
POST   /api/v1/deals                    # Create deal
GET    /api/v1/deals/{id}               # Deal details
PATCH  /api/v1/deals/{id}/stage         # Move to stage
PATCH  /api/v1/deals/{id}/close         # Win/lose deal
```

### Meetings APIs
```
GET    /api/v1/meetings                 # List meetings
POST   /api/v1/meetings                 # Schedule meeting
PATCH  /api/v1/meetings/{id}            # Update meeting
POST   /api/v1/meetings/{id}/complete   # Mark completed
```

### Activities APIs
```
GET    /api/v1/activities               # List timeline
POST   /api/v1/activities               # Log activity
GET    /api/v1/activities?company_id={id}  # Company timeline
```

---

**CRM & Pipeline Module = 70% Complete**

✅ **Database schema**: Solid foundation  
✅ **Sample data**: 12 leads from Discovery  
⚠️ **Missing tables**: deal_stages, tasks, call_logs, notes  
⚠️ **Data flow**: Needs lead→company conversion  
⚠️ **Frontend**: Needs testing and verification

**Ready to convert leads to customers! 🎯**
