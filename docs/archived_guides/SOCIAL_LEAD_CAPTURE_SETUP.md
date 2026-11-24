# 🌐 Social Media Lead Capture - Setup & Configuration Guide

**Complete guide for capturing leads from Instagram, Facebook, Twitter, LinkedIn, Email, and WhatsApp.**

---

## 📋 Overview

System ab automatically leads capture karega from:
- 📸 **Instagram** - Comments, DMs, Story replies
- 📘 **Facebook** - Post comments, Page messages  
- 🐦 **X (Twitter)** - Mentions, Replies, DMs
- 💼 **LinkedIn** - Comments, InMail, Connection requests
- ✉️ **Email Replies** - Incoming email responses
- 💬 **WhatsApp** - Business API messages

---

## 🗄️ Database Schema

### Tables Created

**1. `social_media_leads`**
```sql
• platform (INSTAGRAM, FACEBOOK, TWITTER, LINKEDIN)
• social_profile_url, social_username
• message_content, engagement_type
• sentiment, interest_score
• processed, lead_id (FK to business_leads)
```

**2. `inbound_messages`**
```sql
• channel (EMAIL, WHATSAPP, SMS)
• sender_contact (email/phone)
• message_body, subject
• interest_score, sentiment, classification
• processed, lead_id
```

### Migration Status
✅ **Migration 007** successfully applied  
✅ Tables created with indexes  
✅ Foreign keys to business_leads configured

---

## 🔑 API Configuration

### Required Credentials

Create `.env` file in `backend/` with:

```env
# ========== Instagram/Facebook ==========
# Get from: https://developers.facebook.com/
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_PAGE_ACCESS_TOKEN=your_fb_page_token

# ========== Twitter (X) ==========
# Get from: https://developer.twitter.com/
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# ========== LinkedIn ==========
# Get from: https://www.linkedin.com/developers/
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token

# ========== WhatsApp Business ==========
# Get from: https://business.whatsapp.com/
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token_123

# ========== Email (IMAP) ==========
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_EMAIL=your-email@gmail.com
IMAP_PASSWORD=your-app-password
IMAP_FOLDER=INBOX

# ========== Email (SendGrid Webhook - Optional) ==========
SENDGRID_WEBHOOK_SECRET=your_sendgrid_secret
```

---

## 🚀 Platform Setup Instructions

### 1. Instagram Setup

**Step 1: Create Facebook App**
1. Go to https://developers.facebook.com/
2. Create new app → Business type
3. Add Instagram Graph API product

**Step 2: Get Access Token**
1. Graph API Explorer → Select your app
2. Add permissions: `pages_show_list`, `instagram_basic`, `instagram_manage_messages`
3. Generate Access Token
4. Copy to `.env` as `INSTAGRAM_ACCESS_TOKEN`

**Step 3: Connect Instagram Business Account**
1. Link Instagram account to Facebook Page
2. Get Page ID from Page Settings
3. Copy to `.env` as `FACEBOOK_PAGE_ID`

### 2. Facebook Setup

**Step 1: Facebook Page Access**
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app
3. Add permissions: `pages_manage_engagement`, `pages_read_user_content`, `pages_messaging`
4. Generate Page Access Token
5. Copy to `.env` as `FACEBOOK_PAGE_ACCESS_TOKEN`

### 3. Twitter (X) Setup

**Step 1: Create Twitter Developer Account**
1. Go to https://developer.twitter.com/
2. Apply for Developer Account (Elevated access recommended)

**Step 2: Create App**
1. Developer Portal → Projects & Apps → Create App
2. Enable OAuth 1.0a with Read + Write permissions

**Step 3: Get Credentials**
1. Keys and Tokens tab
2. Copy:
   - API Key → `TWITTER_API_KEY`
   - API Secret → `TWITTER_API_SECRET`
   - Bearer Token → `TWITTER_BEARER_TOKEN`
   - Access Token → `TWITTER_ACCESS_TOKEN`
   - Access Secret → `TWITTER_ACCESS_SECRET`

### 4. LinkedIn Setup

**Step 1: Create LinkedIn App**
1. Go to https://www.linkedin.com/developers/
2. Create App → Fill company details
3. Products: Add "Sign In with LinkedIn" + "Marketing Developer Platform"

**Step 2: Get OAuth Credentials**
1. Auth tab → Copy Client ID and Secret
2. Redirect URLs: Add `http://localhost:8000/auth/linkedin/callback`

**Step 3: Generate Access Token**
```powershell
# Use LinkedIn OAuth flow or Postman
# Guide: https://docs.microsoft.com/en-us/linkedin/shared/authentication/
```

### 5. WhatsApp Business Setup

**Step 1: Meta Business Account**
1. Go to https://business.facebook.com/
2. Create Business Account
3. Add WhatsApp product

**Step 2: WhatsApp Business API**
1. Developer Portal → Create App → Business type
2. Add WhatsApp product
3. Get Test Phone Number or Add your own

**Step 3: Configure Webhook**
1. WhatsApp → Configuration
2. Callback URL: `https://yourdomain.com/api/v1/webhooks/whatsapp`
3. Verify Token: Set custom token (match `.env`)
4. Subscribe to: `messages`, `message_status`

**Step 4: Get Credentials**
1. Copy Phone Number ID → `WHATSAPP_PHONE_NUMBER_ID`
2. Generate Access Token → `WHATSAPP_ACCESS_TOKEN`

### 6. Email Setup (IMAP)

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Google Account → Security → App Passwords
   - Create password for "Mail"
3. Copy to `.env` as `IMAP_PASSWORD`

**Other Providers:**
- Outlook: `imap-mail.outlook.com:993`
- Yahoo: `imap.mail.yahoo.com:993`

---

## ⚙️ Celery Tasks Configuration

### Polling Tasks Added

System automatically polls these platforms:

```python
# In backend/app/workers/celery_app.py beat_schedule

'poll-instagram-leads': {
    'task': 'poll_instagram_leads_task',
    'schedule': 300.0,  # Every 5 minutes
}

'poll-facebook-leads': {
    'task': 'poll_facebook_leads_task',
    'schedule': 300.0,  # Every 5 minutes
}

'poll-twitter-leads': {
    'task': 'poll_twitter_leads_task',
    'schedule': 300.0,  # Every 5 minutes
}

'poll-linkedin-leads': {
    'task': 'poll_linkedin_leads_task',
    'schedule': 600.0,  # Every 10 minutes
}

'process-email-inbox': {
    'task': 'process_email_inbox_task',
    'schedule': 120.0,  # Every 2 minutes
}
```

### Celery Configuration Required

**Update: `backend/app/workers/celery_app.py`**

Add imports:
```python
from app.workers.social_polling_tasks import (
    poll_instagram_leads_task,
    poll_facebook_leads_task,
    poll_twitter_leads_task,
    poll_linkedin_leads_task,
    process_email_inbox_task,
)
```

### Restart Celery

```powershell
# Stop current Celery worker and beat (Ctrl+C on both terminals)

# Restart Worker
cd d:\MVP\backend
.\venv\Scripts\celery.exe -A app.workers.celery_app worker -l info -P solo --concurrency=2

# Restart Beat
cd d:\MVP\backend
.\venv\Scripts\celery.exe -A app.workers.celery_app beat -l info
```

---

## 📡 Webhook Endpoints

### WhatsApp Webhook

**Endpoint:** `POST /api/v1/webhooks/whatsapp`

**Verification (GET request):**
```
GET /api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.challenge=123&hub.verify_token=your_token
```

**Message Webhook (POST):**
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "919876543210",
          "text": {"body": "I'm interested"},
          "timestamp": "1234567890"
        }]
      }
    }]
  }]
}
```

### Email Webhook (SendGrid - Optional)

**Endpoint:** `POST /api/v1/webhooks/email`

**Inbound Parse:**
```json
{
  "from": "user@example.com",
  "to": "your-email@domain.com",
  "subject": "Re: Your offer",
  "text": "Yes, I'm interested. Send pricing.",
  "headers": "...",
  "attachments": 0
}
```

---

## 🧪 Testing

### Test Instagram Lead Capture

1. **Post on Instagram connected account**
2. **Comment from test account**: "I'm interested in this!"
3. **Wait 5 minutes** for polling task
4. **Check database**:
```sql
SELECT * FROM social_media_leads 
WHERE platform = 'INSTAGRAM' 
ORDER BY created_at DESC 
LIMIT 5;
```

### Test WhatsApp

```powershell
# Send test message via WhatsApp Business API
curl -X POST "https://graph.facebook.com/v18.0/$PHONE_NUMBER_ID/messages" `
  -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{
    "messaging_product": "whatsapp",
    "to": "YOUR_TEST_NUMBER",
    "type": "text",
    "text": {"body": "Test message"}
  }'
```

### Test Email Capture

1. **Send email reply** to configured IMAP inbox
2. **Wait 2 minutes** for polling task
3. **Check database**:
```sql
SELECT * FROM inbound_messages 
WHERE channel = 'EMAIL' 
ORDER BY received_at DESC 
LIMIT 5;
```

---

## 📊 API Usage

### Get All Social Leads

```powershell
$headers = @{"X-API-Key"="test-api-key-2025"}
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social-leads" `
  -Headers $headers
```

### Filter by Platform

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social-leads?platform=INSTAGRAM" `
  -Headers $headers
```

### Get Social Lead Stats

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social-leads/stats" `
  -Headers $headers
```

**Response:**
```json
{
  "total": 150,
  "by_platform": {
    "INSTAGRAM": 60,
    "FACEBOOK": 40,
    "TWITTER": 30,
    "LINKEDIN": 20
  },
  "unprocessed": 25,
  "today": 15
}
```

### Get Inbound Messages

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/social-leads/inbound-messages" `
  -Headers $headers
```

---

## 🔄 Automation Flow

### Social Media Flow

```
1. User comments on Instagram post: "I'm interested!"
   ↓
2. Celery task polls Instagram API (every 5 mins)
   ↓
3. Extracts: @username, profile URL, comment text
   ↓
4. Sentiment analysis: INTERESTED (score: 0.85)
   ↓
5. Creates record in social_media_leads table
   ↓
6. Checks if lead exists in business_leads
   ↓
7a. If NOT exists → Creates new lead
7b. If exists → Updates existing lead
   ↓
8. Fires NEW_LEAD or LEAD_UPDATED event
   ↓
9. Workflow automation runs:
   - Auto-qualification
   - Lead scoring
   - CRM enrichment
   - Outreach queueing
```

### Email Reply Flow

```
1. Customer replies to outreach email
   ↓
2. Celery task checks IMAP inbox (every 2 mins)
   ↓
3. Parses: sender email, subject, body
   ↓
4. Keyword detection: "interested", "pricing" → INTERESTED
   ↓
5. Creates record in inbound_messages table
   ↓
6. Finds matching lead by email
   ↓
7. Fires REPLY_CLASSIFIED event (already wired)
   ↓
8. Workflow runs:
   - Updates lead status
   - Assigns to sales rep
   - Queues follow-up
```

### WhatsApp Flow

```
1. Customer sends WhatsApp message
   ↓
2. WhatsApp webhook hits /webhooks/whatsapp
   ↓
3. Validates webhook signature
   ↓
4. Extracts: phone number, message, timestamp
   ↓
5. Creates record in inbound_messages table
   ↓
6. Finds or creates lead by phone
   ↓
7. Fires NEW_LEAD or LEAD_UPDATED event
   ↓
8. Auto-response queued (if configured)
```

---

## 🛡️ Security Best Practices

### API Token Storage
- ✅ Store all tokens in `.env` file
- ✅ Add `.env` to `.gitignore`
- ✅ Never commit tokens to Git
- ✅ Rotate tokens every 90 days

### Webhook Verification
- ✅ WhatsApp: Verify `hub.verify_token`
- ✅ SendGrid: Verify webhook signature
- ✅ Reject invalid requests

### Rate Limiting
- ✅ Instagram: 200 calls/hour per user
- ✅ Facebook: 200 calls/hour per page
- ✅ Twitter: 900 requests/15 mins
- ✅ LinkedIn: 500 calls/day per app

System automatically handles rate limits with exponential backoff.

---

## 🐛 Troubleshooting

### Instagram Not Capturing Leads

**Check:**
```powershell
# Celery worker logs for errors
# Terminal showing Celery worker

# Verify credentials
$headers = @{"Authorization"="Bearer $INSTAGRAM_ACCESS_TOKEN"}
Invoke-RestMethod -Uri "https://graph.facebook.com/v18.0/me" -Headers $headers
```

**Common Issues:**
- Access token expired → Regenerate token
- Permissions missing → Add Instagram permissions
- Instagram not linked → Connect Instagram to FB Page

### WhatsApp Webhook Not Receiving

**Check:**
1. Webhook URL is publicly accessible (use ngrok for local testing)
2. Verify token matches `.env` value
3. Check Meta Developer Console → Webhooks → Subscriptions

**Ngrok Setup (for local testing):**
```powershell
ngrok http 8000
# Copy HTTPS URL → Meta Webhook Configuration
```

### Email Not Processing

**Check IMAP Connection:**
```python
import imaplib
imap = imaplib.IMAP4_SSL('imap.gmail.com')
imap.login('your-email@gmail.com', 'your-app-password')
imap.select('INBOX')
```

**Common Issues:**
- 2FA not enabled → Enable and create app password
- IMAP disabled → Enable in Gmail settings
- Firewall blocking → Allow port 993

---

## 📈 Monitoring

### Check Celery Logs

```powershell
# Watch for task execution
# Terminal 1 (Worker): Shows task processing
# Look for: "Task succeeded" or "Task failed"
```

### Database Queries

**Captured leads today:**
```sql
SELECT COUNT(*) 
FROM social_media_leads 
WHERE created_at::date = CURRENT_DATE;
```

**Unprocessed leads:**
```sql
SELECT platform, COUNT(*) 
FROM social_media_leads 
WHERE processed = FALSE 
GROUP BY platform;
```

**Recent inbound messages:**
```sql
SELECT channel, sender_contact, message_body, sentiment
FROM inbound_messages 
ORDER BY received_at DESC 
LIMIT 10;
```

---

## 🎯 Success Metrics

After setup, you should see:

✅ Celery tasks running every 2-10 minutes  
✅ Social engagement captured within 5 minutes  
✅ Email replies processed within 2 minutes  
✅ WhatsApp messages instant (webhook)  
✅ Leads auto-created with proper source attribution  
✅ NEW_LEAD events triggering workflows  
✅ Interest scores calculated automatically  

---

## 📚 Related Documentation

- **Main Setup:** `DISCOVERY_AUTOMATION_SETUP.md`
- **System Status:** `SYSTEM_RUNNING.md`
- **Technical Design:** `.agents/tasks/social-lead-capture/TECHNICAL_DESIGN.md`
- **API Docs:** http://localhost:8000/docs

---

## 🎊 You're Ready!

Your multi-channel lead capture system is configured. Configure credentials aur Celery restart karo, leads automatically capture hone lagenge!

**Next Steps:**
1. Fill `.env` with API credentials
2. Restart Celery worker + beat
3. Test each platform
4. Monitor Celery logs
5. Check database for captured leads

**Happy Lead Capturing! 🚀**

---

**Last Updated:** November 11, 2026  
**Version:** 1.0.0  
**Workflow:** wf_37f51b539696e9ed
