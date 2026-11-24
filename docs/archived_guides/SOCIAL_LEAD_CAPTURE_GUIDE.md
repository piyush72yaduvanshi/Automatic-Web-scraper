# Social Media & Inbound Lead Capture System - Setup Guide

## Overview

This system automatically captures leads from:
- **Social Media**: Instagram, Facebook, Twitter/X, LinkedIn (comments, DMs, mentions)
- **Email Replies**: IMAP polling or webhook-based (SendGrid, Mailgun)
- **WhatsApp**: Business API webhook integration

All captured leads are automatically scored for interest level and converted to business leads when qualified.

---

## Architecture

### Components
1. **Database Tables**: `social_media_leads`, `inbound_messages`
2. **Celery Tasks**: Scheduled polling tasks (every 2-10 minutes)
3. **API Endpoints**: `/api/v1/social-leads/*`
4. **Webhook Receivers**: WhatsApp & Email webhooks

### Data Flow
1. **Polling Tasks** → Fetch engagements from platform APIs
2. **Store** → Save to `social_media_leads` or `inbound_messages`
3. **Classify** → Calculate interest score & sentiment
4. **Convert** → High-interest engagements → `business_leads`
5. **Fire Events** → `SOCIAL_ENGAGEMENT_DETECTED`, `EMAIL_REPLY_RECEIVED`, `WHATSAPP_MESSAGE_RECEIVED`

---

## Platform Setup

### 1. Instagram Lead Capture

#### Prerequisites
- Facebook Business Account
- Instagram Business Account (linked to Facebook)
- Facebook App with Instagram permissions

#### Setup Steps

1. **Create Facebook App**
   - Go to https://developers.facebook.com/apps/
   - Create new app → Type: Business
   - Add "Instagram Graph API" product

2. **Get Access Token**
   - Go to Graph API Explorer
   - Select your app
   - Request permissions: `instagram_basic`, `instagram_manage_comments`, `instagram_manage_messages`
   - Generate long-lived token (60 days)

3. **Get Business Account ID**
   ```bash
   curl "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_TOKEN"
   ```
   Find your Instagram Business Account ID in the response

4. **Add to .env**
   ```env
   INSTAGRAM_ACCESS_TOKEN=your_long_lived_token_here
   INSTAGRAM_BUSINESS_ACCOUNT_ID=your_business_account_id
   ```

5. **Token Refresh** (every 60 days)
   ```bash
   curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN"
   ```

#### Rate Limits
- **200 calls/hour** per user
- System retries with exponential backoff

---

### 2. Facebook Page Lead Capture

#### Prerequisites
- Facebook Page
- Facebook App with Pages permissions

#### Setup Steps

1. **Create Facebook App** (if not done for Instagram)

2. **Get Page Access Token**
   - Graph API Explorer → Select your app
   - Request permissions: `pages_read_engagement`, `pages_manage_metadata`, `pages_messaging`
   - Get token for your page

3. **Get Page ID**
   ```bash
   curl "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_USER_TOKEN"
   ```

4. **Add to .env**
   ```env
   FACEBOOK_PAGE_ACCESS_TOKEN=your_page_token_here
   FACEBOOK_PAGE_ID=your_page_id
   ```

#### Rate Limits
- **200 calls/hour** per user
- System monitors rate limit headers

---

### 3. Twitter/X Lead Capture

#### Prerequisites
- Twitter Developer Account (elevated access recommended)
- Twitter App

#### Setup Steps

1. **Create Twitter App**
   - Go to https://developer.twitter.com/en/portal/dashboard
   - Create project and app

2. **Generate Bearer Token**
   - App settings → Keys and tokens
   - Generate Bearer Token

3. **Get Your User ID**
   ```bash
   curl -H "Authorization: Bearer YOUR_BEARER_TOKEN" "https://api.twitter.com/2/users/by/username/YOUR_USERNAME"
   ```

4. **Add to .env**
   ```env
   TWITTER_BEARER_TOKEN=your_bearer_token_here
   TWITTER_USER_ID=your_user_id
   ```

#### Rate Limits
- **75 requests per 15 minutes** for mentions
- System respects `x-rate-limit-reset` header

---

### 4. LinkedIn Lead Capture

#### Prerequisites
- LinkedIn Company Page
- LinkedIn App with OAuth 2.0

#### Setup Steps

1. **Create LinkedIn App**
   - Go to https://www.linkedin.com/developers/apps
   - Create app → Associate with company page

2. **Request Permissions**
   - Request `r_organization_social` permission
   - Request `w_organization_social` if posting

3. **OAuth 2.0 Flow**
   ```bash
   # Authorization URL
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&scope=r_organization_social

   # Exchange code for token
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d grant_type=authorization_code \
     -d code=YOUR_AUTH_CODE \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d redirect_uri=YOUR_REDIRECT_URI
   ```

4. **Get Organization URN**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee"
   ```

5. **Add to .env**
   ```env
   LINKEDIN_ACCESS_TOKEN=your_access_token_here
   LINKEDIN_ORG_ID=your_org_id
   ```

#### Rate Limits
- **500 requests/day** per user
- System polls every 10 minutes (slower than others)

---

### 5. WhatsApp Business API

#### Prerequisites
- WhatsApp Business Account
- Meta Business Account
- Verified phone number

#### Setup Steps

1. **Create WhatsApp Business App**
   - Go to https://developers.facebook.com/apps/
   - Add WhatsApp product

2. **Configure Webhook**
   - Webhook URL: `https://yourdomain.com/api/v1/social-leads/webhooks/whatsapp`
   - Verify token: Set a random string (save it!)
   - Subscribe to `messages` webhook field

3. **Get Credentials**
   - Phone Number ID: In WhatsApp dashboard
   - Access Token: Generate permanent token
   - App Secret: In app settings → Basic

4. **Add to .env**
   ```env
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   WHATSAPP_ACCESS_TOKEN=your_access_token
   WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
   WHATSAPP_APP_SECRET=your_app_secret
   ```

5. **Webhook Verification**
   - Meta will send GET request to verify endpoint
   - System automatically responds with challenge

#### Testing
```bash
# Test webhook (from Meta)
curl -X GET "https://yourdomain.com/api/v1/social-leads/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=12345"
# Should return: 12345
```

---

### 6. Email Reply Capture (IMAP)

#### Prerequisites
- Email account with IMAP access
- App-specific password (for Gmail, Outlook)

#### Setup Steps (Gmail)

1. **Enable IMAP**
   - Gmail Settings → Forwarding and POP/IMAP
   - Enable IMAP

2. **Create App Password**
   - Google Account → Security → 2-Step Verification
   - App passwords → Generate for "Mail"

3. **Add to .env**
   ```env
   IMAP_SERVER=imap.gmail.com
   IMAP_PORT=993
   IMAP_EMAIL=your_email@gmail.com
   IMAP_PASSWORD=your_app_password
   ```

#### Setup Steps (Outlook)

```env
IMAP_SERVER=outlook.office365.com
IMAP_PORT=993
IMAP_EMAIL=your_email@outlook.com
IMAP_PASSWORD=your_password
```

---

### 7. Email Webhook (SendGrid)

#### Prerequisites
- SendGrid account
- Inbound Parse configured

#### Setup Steps

1. **Configure Inbound Parse**
   - SendGrid Dashboard → Settings → Inbound Parse
   - Hostname: mail.yourdomain.com (configure DNS MX record)
   - Destination URL: `https://yourdomain.com/api/v1/social-leads/webhooks/email`

2. **Set Webhook Secret**
   - Settings → Mail Settings → Event Webhook
   - Generate signing key

3. **Add to .env**
   ```env
   SENDGRID_WEBHOOK_SECRET=your_webhook_secret
   ```

---

## Running the System

### 1. Start Backend Server

```powershell
cd d:\MVP\backend
.\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Celery Workers

```powershell
cd d:\MVP\backend
.\venv\Scripts\celery.exe -A app.workers.celery_app worker --pool=solo --loglevel=info
```

### 3. Start Celery Beat (Scheduler)

```powershell
cd d:\MVP\backend
.\venv\Scripts\celery.exe -A app.workers.celery_app beat --loglevel=info
```

---

## API Endpoints

### List Social Leads
```bash
GET /api/v1/social-leads?platform=INSTAGRAM&days_back=7
Authorization: Bearer YOUR_API_KEY
```

### Social Lead Statistics
```bash
GET /api/v1/social-leads/stats?days_back=30
Authorization: Bearer YOUR_API_KEY
```

### List Inbound Messages
```bash
GET /api/v1/social-leads/inbound-messages?channel=EMAIL&classification=INTERESTED
Authorization: Bearer YOUR_API_KEY
```

### Inbound Message Statistics
```bash
GET /api/v1/social-leads/inbound-messages/stats
Authorization: Bearer YOUR_API_KEY
```

### Manual Social Lead Creation
```bash
POST /api/v1/social-leads/manual
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "platform": "INSTAGRAM",
  "social_username": "example_user",
  "social_profile_url": "https://instagram.com/example_user",
  "message_content": "I'm interested in your product!",
  "engagement_type": "COMMENT"
}
```

---

## Monitoring & Troubleshooting

### Check Celery Task Status

```bash
# View active tasks
curl http://localhost:8000/api/v1/health

# Check Redis
redis-cli
> KEYS celery*
```

### View Logs

```powershell
# Backend logs
Get-Content d:\MVP\backend\logs\app.log -Tail 100 -Wait

# Celery logs
# Check console output of celery worker
```

### Common Issues

#### 1. Instagram Token Expired
**Error**: `AuthenticationError: Invalid access token`
**Fix**: Regenerate long-lived token (see Instagram setup)

#### 2. Rate Limit Exceeded
**Error**: `RateLimitError: Rate limit exceeded`
**Fix**: System auto-retries. Check logs for retry schedule.

#### 3. WhatsApp Webhook Not Receiving
**Error**: No messages appearing
**Fix**: 
- Verify webhook URL is publicly accessible
- Check webhook signature validation
- Test with Meta's webhook tester

#### 4. Celery Beat Not Running
**Error**: No scheduled tasks executing
**Fix**: Ensure Celery Beat process is running separately from workers

---

## Event Integration

### Workflow Triggers

The system emits events that can trigger workflows:

1. **SOCIAL_ENGAGEMENT_DETECTED**
   - Fired when high-interest social engagement captured
   - Payload: `engagement_id`, `lead_id`, `platform`, `interest_score`

2. **EMAIL_REPLY_RECEIVED**
   - Fired when email reply classified
   - Payload: `message_id`, `classification`, `sentiment`

3. **WHATSAPP_MESSAGE_RECEIVED**
   - Fired when WhatsApp message received
   - Payload: `message_id`, `sender`, `message_preview`

### Example Workflow

Create workflow in UI or database:
```sql
INSERT INTO workflow_definitions (name, trigger_type, steps_config, is_active) 
VALUES (
  'Notify Sales on Interested Reply',
  'EMAIL_REPLY_RECEIVED',
  '[{"agent": "notify", "config": {"channel": "slack"}}]',
  true
);
```

---

## Security Best Practices

1. **Never commit API keys** to git
2. **Use webhook signature validation** for all webhooks
3. **Rotate tokens regularly** (every 60-90 days)
4. **Monitor rate limits** to avoid API bans
5. **Use HTTPS** for all webhook endpoints
6. **Implement IP whitelisting** if possible

---

## Performance Optimization

### Recommended Settings

```env
# Celery
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_TASK_TIME_LIMIT=300

# Database
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Scaling

- **Horizontal**: Add more Celery workers
- **Vertical**: Increase task concurrency
- **Rate Limiting**: Adjust polling frequency per platform limits

---

## Support & Resources

- **Instagram Graph API**: https://developers.facebook.com/docs/instagram-api
- **Facebook Graph API**: https://developers.facebook.com/docs/graph-api
- **Twitter API v2**: https://developer.twitter.com/en/docs/twitter-api
- **LinkedIn API**: https://learn.microsoft.com/en-us/linkedin/
- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp

---

## Next Steps

1. Configure at least one social platform (start with easiest: Twitter)
2. Test webhook endpoints with platform test tools
3. Monitor Celery logs for successful polling
4. Create workflows to act on captured leads
5. Build frontend dashboard for lead review

Good luck! 🚀
