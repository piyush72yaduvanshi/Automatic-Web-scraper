# 🎯 Marketing & SEO Module - Testing Guide

**Date**: November 12, 2026  
**Status**: Ready for Testing

---

## 📋 Pre-Testing Checklist

✅ **Backend Running**: Terminal 12, Port 8000  
✅ **Frontend Running**: Terminal 6, Port 5173  
✅ **PostgreSQL**: Docker container active  
✅ **Redis**: Docker container active  
✅ **Celery Worker**: Terminal 8, 12 tasks loaded  
✅ **Celery Beat**: Terminal 7, scheduler active

---

## 🎨 Test 1: Content & Social Module

### Step 1.1: View Social Accounts
```
1. Browser: http://localhost:5173
2. Navigate to: Marketing → Content & Social
3. Expected: ContentSocialView.tsx page loads
4. Look for: Social Accounts section
```

**Expected Data:**
- 5 accounts visible
- Facebook: Acme Corporate Page (3,400 followers)
- Instagram: @acme_official (1,250 followers)
- Twitter: @acmeworks (5,800 followers)
- LinkedIn Company: Acme Technologies (12,400 followers)
- LinkedIn Personal: Founder Profile (8,900 followers)
- Status: All showing "NOT_CONFIGURED" or "Connect OAuth"

### Step 1.2: View Pending Social Posts
```
In the same ContentSocialView page:
1. Scroll to "Pending Posts" or "Approval Queue"
2. Expected: 5 posts visible
```

**Expected Posts:**
| Platform | Status | Preview |
|---------|--------|---------|
| LinkedIn Company | DRAFT | "We are proud to announce..." |
| Instagram | PENDING_APPROVAL | "Efficiency isn't about working more hours..." |
| Facebook | PENDING_APPROVAL | "Most sales teams spend 65% of their working hours..." |
| Twitter | PENDING_APPROVAL | "Your sales stack shouldn't require 10 fragmented tools..." |
| LinkedIn Personal | PENDING_APPROVAL | "Unpopular opinion in B2B sales..." |

### Step 1.3: Test Post Approval (Frontend)
```
1. Click on any PENDING_APPROVAL post
2. Click "Approve" or "Edit & Approve" button
3. Set schedule date/time (or leave for immediate)
4. Expected: Status changes to SCHEDULED
5. Check database:
```

**Verify in Database:**
```powershell
$query = "SELECT id, platform, status, scheduled_for FROM social_posts WHERE status = 'SCHEDULED';"
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c $query
```

### Step 1.4: Test Post Publishing (Backend API)
```powershell
# Direct API test for post approval
$postId = "get-from-database-or-frontend"  # UUID of a pending post

$body = @{
    action = "approve"
    scheduled_for = (Get-Date).AddMinutes(2).ToString("yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social/posts/$postId/approve" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Expected Response:**
```json
{
  "id": "uuid",
  "status": "SCHEDULED",
  "scheduled_for": "2026-11-12T20:30:00",
  "message": "Post approved and scheduled"
}
```

### Step 1.5: Monitor Celery Publishing
```powershell
# Watch Celery worker logs (Terminal 8)
# When scheduled_for time arrives, Celery Beat will trigger publishing task
# Look for: "Publishing post to LINKEDIN_ORG..."
```

**⚠️ Note:** Actual publishing will fail without OAuth tokens. Expected error:
```
[ERROR] Failed to publish: OAuth token missing for account
```

This is **NORMAL** - OAuth setup needed for real publishing.

---

## 🔍 Test 2: SEO Module

### Step 2.1: View SEO Projects
```
1. Browser: http://localhost:5173
2. Navigate to: Marketing → SEO
3. Expected: SEOView.tsx page loads
```

**Expected Data:**
- 1 Project: "AI Sales & CRM Operating System"
- Domain: ai-sales-crm.io
- Location: United States
- GSC Status: Not Connected

### Step 2.2: View SEO Keywords
```
In SEOView page:
1. Click on the project "AI Sales & CRM Operating System"
2. Navigate to "Keywords" tab
3. Expected: 3 keywords visible
```

**Verify Keywords in Database:**
```powershell
$query = @"
SELECT 
    keyword, 
    cluster_name,
    search_intent,
    search_volume, 
    difficulty_score,
    status
FROM seo_keywords
ORDER BY search_volume DESC;
"@

docker exec crm_leads_postgres psql -U postgres -d crm_leads -c $query
```

### Step 2.3: Add New Keyword (Frontend Test)
```
1. In Keywords section, click "Add Keyword"
2. Fill form:
   - Keyword: "AI sales automation software"
   - Cluster: "Product Features"
   - Search Intent: TRANSACTIONAL
   - Search Volume: 2400
   - Difficulty: 0.65
   - Target Page Type: Landing Page
3. Click "Save"
4. Expected: New keyword appears in list
```

### Step 2.4: Test Keyword API (Backend)
```powershell
# Add keyword via API
$body = @{
    project_id = "e4a966a7-6808-4acb-a4e6-b791bacd05ac"  # From database
    keyword = "best CRM for AI sales teams"
    cluster_name = "Product Comparison"
    search_intent = "INFORMATIONAL"
    search_volume = 1800
    difficulty_score = 0.58
    target_page_type = "Blog Post"
    status = "RESEARCH"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/seo/keywords" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Expected Response:**
```json
{
  "id": "new-uuid",
  "keyword": "best CRM for AI sales teams",
  "status": "RESEARCH",
  "created_at": "2026-11-12T19:45:00"
}
```

---

## 📥 Test 3: Inbound Message Capture

### Step 3.1: Simulate Inbound Message (API Test)
```powershell
# Simulate Instagram DM from potential customer
$body = @{
    platform = "INSTAGRAM"
    sender_handle = "@john_entrepreneur"
    sender_name = "John Smith"
    message_content = "Hi! I'm interested in your AI CRM. Can we schedule a demo? My email is john@startup.com"
    received_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    message_type = "DIRECT_MESSAGE"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/inbound/messages" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$response
```

**Expected Response:**
```json
{
  "id": "uuid",
  "platform": "INSTAGRAM",
  "sender_handle": "@john_entrepreneur",
  "status": "NEW",
  "created_at": "2026-11-12T19:50:00"
}
```

### Step 3.2: Check if Workflow Triggered
```powershell
# Check if message was processed
$query = "SELECT * FROM inbound_messages ORDER BY created_at DESC LIMIT 1;"
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c $query

# Check if lead was created
$query2 = "SELECT * FROM business_leads WHERE source = 'INBOUND_SOCIAL' ORDER BY created_at DESC LIMIT 1;"
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c $query2

# Check if workflow executed
$query3 = @"
SELECT 
    we.workflow_name,
    we.status,
    we.trigger_event,
    we.created_at
FROM workflow_executions we
WHERE we.trigger_event = 'REPLY_CLASSIFIED'
ORDER BY we.created_at DESC LIMIT 1;
"@
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c $query3
```

**Expected Flow:**
1. Message saved to `inbound_messages`
2. Celery task processes message
3. Detects interest keywords: "interested", "demo", "pricing"
4. Creates new record in `business_leads`
5. Triggers workflow: "Escalate Interested Inbound Reply"
6. Lead auto-assigned to sales rep

---

## 🗄️ Test 4: MinIO Storage

### Step 4.1: Check MinIO Service
```powershell
# Check if MinIO is accessible
Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -Method GET
```

**Expected:** HTTP 200 OK

### Step 4.2: Test Image Upload (API)
```powershell
# Create test image file
$testImagePath = "d:\MVP\test-image.png"
# (You need an actual image file here)

# Upload to backend API
$form = @{
    file = Get-Item -Path $testImagePath
    folder = "social-posts"
}

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/media/upload" `
    -Method POST `
    -Form $form

$response
```

**Expected Response:**
```json
{
  "url": "http://localhost:9000/crm-social-media/social-posts/uuid-filename.png",
  "bucket": "crm-social-media",
  "object_name": "social-posts/uuid-filename.png"
}
```

### Step 4.3: Attach Media to Social Post
```powershell
$postId = "get-post-uuid"
$mediaUrl = "http://localhost:9000/crm-social-media/social-posts/image.png"

$body = @{
    media_urls = @($mediaUrl)
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social/posts/$postId" `
    -Method PATCH `
    -ContentType "application/json" `
    -Body $body
```

**Verify:**
```powershell
$query = "SELECT id, platform, media_urls_json FROM social_posts WHERE id = '$postId';"
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c $query
```

---

## 📊 Test 5: Social Post Metrics (Future)

### Step 5.1: Simulate Metrics Fetch
```powershell
# After a post is published, Celery fetches metrics
# Simulate manual metrics update

$postId = "published-post-uuid"
$body = @{
    impressions = 15420
    reach = 12300
    engagement_count = 487
    likes = 312
    comments = 45
    shares = 89
    clicks = 41
    saves = 23
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social/posts/$postId/metrics" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Verify:**
```powershell
$query = "SELECT * FROM social_post_metrics WHERE post_id = '$postId';"
docker exec crm_leads_postgres psql -U postgres -d crm_leads -c $query
```

---

## 🔗 Test 6: OAuth Integration (Advanced)

### Step 6.1: Check OAuth Endpoints
```powershell
# List available OAuth routes
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social/oauth/providers" -Method GET
```

**Expected Response:**
```json
{
  "providers": [
    "FACEBOOK",
    "INSTAGRAM",
    "TWITTER",
    "LINKEDIN_ORG",
    "LINKEDIN_PERSONAL"
  ]
}
```

### Step 6.2: Initiate OAuth Flow (Frontend)
```
1. In ContentSocialView page
2. Click "Connect" on Facebook account
3. Expected: Redirect to Facebook OAuth page
4. Authorize app
5. Redirect back with access_token
6. Backend saves token to social_accounts
7. Status changes to ACTIVE
```

**⚠️ Prerequisite:**
You need Facebook/Instagram/Twitter/LinkedIn developer apps configured with:
- App ID & App Secret
- Redirect URI: http://localhost:8000/api/v1/social/oauth/callback/{platform}
- Required permissions granted

---

## 📈 Test Results Summary

### ✅ What Should Work Now

| Test | Expected Result | Pass/Fail |
|------|----------------|-----------|
| View Social Accounts | 5 accounts visible with NOT_CONFIGURED status | [ ] |
| View Pending Posts | 5 posts in approval queue | [ ] |
| Approve Post (UI) | Status changes to SCHEDULED | [ ] |
| SEO Project View | 1 project with 3 keywords | [ ] |
| Add New Keyword | Keyword saved and visible | [ ] |
| Inbound Message API | Message saved to database | [ ] |
| Workflow Trigger | Lead created from inbound message | [ ] |
| MinIO Health Check | HTTP 200 response | [ ] |

### ⚠️ What Needs OAuth Setup

| Feature | Blocker | Solution |
|---------|---------|----------|
| Actual Post Publishing | No access tokens | Complete OAuth flow per platform |
| Metrics Fetching | No API access | OAuth + Platform API credentials |
| Inbound Webhooks | No webhook endpoints registered | Setup webhooks in platform developer consoles |

### ❌ Known Limitations

1. **Publishing will fail** without OAuth - expected behavior
2. **Metrics table empty** - needs published posts first
3. **Inbound capture** - needs webhook setup on platforms
4. **GSC integration** - needs Google API credentials

---

## 🎯 Next Steps After Testing

### If Tests Pass ✅
1. **Document findings**: Which features work end-to-end
2. **Setup OAuth**: Get credentials from each platform
3. **Configure webhooks**: Register URLs in developer consoles
4. **Test real publishing**: Schedule and publish actual post
5. **Monitor metrics**: Verify data collection after publish

### If Tests Fail ❌
1. **Check backend logs**: Terminal 12 for API errors
2. **Check Celery logs**: Terminal 8 for task failures
3. **Check database**: Verify data actually saved
4. **Check frontend console**: Browser DevTools for network errors
5. **Report issues**: Note exact error messages

---

## 📞 API Endpoints Quick Reference

### Social Media APIs
```
GET    /api/v1/social/accounts
POST   /api/v1/social/accounts
GET    /api/v1/social/posts?status=PENDING_APPROVAL
POST   /api/v1/social/posts
POST   /api/v1/social/posts/{id}/approve
GET    /api/v1/social/posts/{id}/metrics
```

### SEO APIs
```
GET    /api/v1/seo/projects
POST   /api/v1/seo/projects
GET    /api/v1/seo/keywords?project_id={uuid}
POST   /api/v1/seo/keywords
PATCH  /api/v1/seo/keywords/{id}
```

### Inbound APIs
```
POST   /api/v1/inbound/messages
GET    /api/v1/inbound/messages?status=NEW
POST   /api/v1/webhooks/facebook
POST   /api/v1/webhooks/instagram
```

### Media APIs
```
POST   /api/v1/media/upload
GET    /api/v1/media/{object_name}
DELETE /api/v1/media/{object_name}
```

---

## 🔍 Debugging Tips

### Backend not responding?
```powershell
# Check if backend process running
Get-Process | Where-Object { $_.ProcessName -like "*python*" }

# Check port 8000
Test-NetConnection -ComputerName localhost -Port 8000
```

### Frontend not loading?
```powershell
# Check if Vite dev server running
Get-Process | Where-Object { $_.ProcessName -like "*node*" }

# Check port 5173
Test-NetConnection -ComputerName localhost -Port 5173
```

### Celery tasks not running?
```powershell
# Check Celery worker logs
# Terminal 8 should show: "celery@HOSTNAME ready"
# If not, restart: celery -A app.workers.celery_app worker --loglevel=info
```

### Database query issues?
```powershell
# Direct PostgreSQL access
docker exec -it crm_leads_postgres psql -U postgres -d crm_leads
# Then run SQL: SELECT * FROM social_posts LIMIT 5;
```

---

**Happy Testing! 🚀**
