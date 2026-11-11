# Multi-Channel Lead Capture System - Technical Design

## Overview

This design extends the existing CRM lead discovery system to capture leads from social media platforms (Instagram, Facebook, Twitter, LinkedIn) and inbound messaging channels (Email replies, WhatsApp). The system will poll social platforms for engagement signals, monitor email replies, and capture WhatsApp messages, automatically converting these interactions into qualified leads in the CRM pipeline.

The architecture leverages the existing PostgreSQL database with pgvector, Celery worker infrastructure, FastAPI async patterns, and the native Python workflow engine. All integrations use official platform APIs with proper authentication, rate limiting, and webhook validation.

---

## Database Schema Design

### 1. New Table: `social_media_leads`

Captures lead-qualifying engagement from social media platforms.

```sql
CREATE TABLE social_media_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Platform Information
    platform VARCHAR(50) NOT NULL,  -- ENUM: INSTAGRAM, FACEBOOK, TWITTER, LINKEDIN
    social_profile_url VARCHAR(500) NOT NULL,
    social_username VARCHAR(200) NOT NULL,
    
    -- Engagement Data
    message_content TEXT,
    engagement_type VARCHAR(100) NOT NULL,  -- comment, dm, mention, reaction, share, profile_visit
    engagement_url VARCHAR(500),  -- Link to the original post/comment
    
    -- Lead Context
    post_context TEXT,  -- Original post content that triggered engagement
    sentiment VARCHAR(50),  -- POSITIVE, NEUTRAL, NEGATIVE, INTERESTED
    interest_score FLOAT DEFAULT 0.5,  -- 0.0 to 1.0 confidence
    
    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    lead_id UUID,  -- FK to business_leads.id once converted
    processing_notes TEXT,
    
    -- Metadata
    platform_user_id VARCHAR(255),  -- Platform's internal user ID
    engagement_timestamp TIMESTAMP NOT NULL,
    metadata JSONB,  -- Platform-specific additional data
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT fk_social_lead_business_lead FOREIGN KEY (lead_id) 
        REFERENCES business_leads(id) ON DELETE SET NULL
);

CREATE INDEX idx_social_media_platform ON social_media_leads(platform);
CREATE INDEX idx_social_media_processed ON social_media_leads(processed);
CREATE INDEX idx_social_media_username ON social_media_leads(social_username);
CREATE INDEX idx_social_media_timestamp ON social_media_leads(engagement_timestamp);
CREATE INDEX idx_social_media_lead_id ON social_media_leads(lead_id);
CREATE UNIQUE INDEX idx_social_media_dedup ON social_media_leads(platform, platform_user_id, engagement_type, engagement_timestamp);
```

### 2. New Table: `inbound_messages`

Captures inbound messages from email replies and WhatsApp.

```sql
CREATE TABLE inbound_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Channel Information
    channel VARCHAR(50) NOT NULL,  -- ENUM: EMAIL, WHATSAPP, SMS
    sender_contact VARCHAR(255) NOT NULL,  -- Email address or phone number
    
    -- Message Content
    message_body TEXT NOT NULL,
    subject VARCHAR(500),  -- For email only
    
    -- Lead Intelligence
    interest_score FLOAT DEFAULT 0.5,
    sentiment VARCHAR(50),  -- POSITIVE, NEUTRAL, NEGATIVE
    classification VARCHAR(100),  -- INTERESTED, OBJECTION, NOT_NOW, UNSUBSCRIBE, QUESTION, OUT_OF_OFFICE
    suggested_reply TEXT,
    
    -- Context
    thread_id VARCHAR(255),  -- Email thread ID or WhatsApp conversation ID
    in_reply_to_message_id VARCHAR(255),  -- Original message this is replying to
    campaign_id UUID,  -- FK to outreach_campaigns if part of campaign
    
    -- Processing
    processed BOOLEAN DEFAULT FALSE,
    lead_id UUID,  -- FK to business_leads.id
    requires_human_attention BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    metadata JSONB,  -- Channel-specific headers, attachments, etc.
    platform_message_id VARCHAR(255),  -- Platform's internal message ID
    
    -- Audit
    received_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    CONSTRAINT fk_inbound_msg_lead FOREIGN KEY (lead_id) 
        REFERENCES business_leads(id) ON DELETE SET NULL,
    CONSTRAINT fk_inbound_msg_campaign FOREIGN KEY (campaign_id)
        REFERENCES outreach_campaigns(id) ON DELETE SET NULL
);

CREATE INDEX idx_inbound_channel ON inbound_messages(channel);
CREATE INDEX idx_inbound_sender ON inbound_messages(sender_contact);
CREATE INDEX idx_inbound_processed ON inbound_messages(processed);
CREATE INDEX idx_inbound_classification ON inbound_messages(classification);
CREATE INDEX idx_inbound_received ON inbound_messages(received_at);
CREATE INDEX idx_inbound_thread ON inbound_messages(thread_id);
CREATE UNIQUE INDEX idx_inbound_dedup ON inbound_messages(channel, platform_message_id);
```

### 3. Modifications to `business_leads` Table

Add new source enum values to track lead origin.

```sql
-- Add new column for lead source type
ALTER TABLE business_leads 
ADD COLUMN IF NOT EXISTS lead_source VARCHAR(50) DEFAULT 'DISCOVERY';

-- Valid values: DISCOVERY, SOCIAL_MEDIA, EMAIL_REPLY, WHATSAPP, MANUAL
CREATE INDEX idx_business_leads_source ON business_leads(lead_source);

-- Add social engagement metadata
ALTER TABLE business_leads 
ADD COLUMN IF NOT EXISTS social_engagement_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_social_engagement_at TIMESTAMP;
```

### 4. Alembic Migration Plan

**Migration File**: `20261104_0001_multi_channel_lead_capture.py`

**Migration Strategy**:
1. Create `social_media_leads` table with all indexes
2. Create `inbound_messages` table with all indexes
3. Alter `business_leads` to add `lead_source`, `social_engagement_count`, `last_social_engagement_at`
4. Create indexes on new columns
5. Backfill existing leads with `lead_source='DISCOVERY'`

**Rollback Strategy**:
- Drop new tables
- Drop new columns from business_leads
- Drop indexes

---

## API Integration Architecture

### 1. Instagram Graph API Integration

**Service**: `app/services/social_capture/instagram_service.py`

**Authentication**: Instagram Access Token (long-lived token via Facebook App)

**Endpoints Used**:
- `GET /{ig-user-id}/media` - Fetch recent posts
- `GET /{media-id}/comments` - Fetch comments on posts
- `GET /{ig-user-id}/conversations` - Fetch direct messages (requires instagram_manage_messages permission)
- `GET /{conversation-id}/messages` - Fetch messages in conversation

**Rate Limits**: 
- 200 requests per user per hour (Tier 1)
- Implement exponential backoff with jitter

**Error Handling**:
- **OAuthException (190)**: Token expired → Log error, disable polling, emit INTEGRATION_HEALTH_CHANGED event → RECOVERABLE if user re-authenticates
- **Rate Limit (4)**: Throttled → Exponential backoff (30s, 60s, 120s, 300s) → RECOVERABLE
- **Permission Denied (10)**: Missing scope → Log error, disable feature → FATAL until re-authorization
- **Invalid Media ID (100)**: Post deleted → Skip and continue → RECOVERABLE
- **Network Timeout**: Retry 3 times with 5s backoff → Log warning → RECOVERABLE

**Data Extraction Pattern**:
```python
async def fetch_instagram_engagements(
    access_token: str,
    instagram_business_id: str,
    since_timestamp: datetime
) -> List[SocialEngagement]:
    # 1. Fetch recent media posts
    # 2. For each post, fetch comments
    # 3. Filter comments by timestamp
    # 4. Fetch DM conversations
    # 5. Extract user profiles and message content
    # 6. Calculate interest score based on keywords and sentiment
    # 7. Return structured engagement list
```

### 2. Facebook Graph API Integration

**Service**: `app/services/social_capture/facebook_service.py`

**Authentication**: Page Access Token

**Endpoints Used**:
- `GET /{page-id}/posts` - Fetch page posts
- `GET /{post-id}/comments` - Fetch comments
- `GET /{page-id}/conversations` - Fetch Messenger conversations
- `GET /{conversation-id}/messages` - Fetch messages

**Rate Limits**:
- 200 calls per user per hour
- Implement token bucket rate limiter

**Error Handling**:
- **OAuthException (190)**: Token expired → Disable integration, notify admin → RECOVERABLE
- **Rate Limit (4/17)**: Throttled → Wait for rate limit reset (header: X-Business-Use-Case-Usage) → RECOVERABLE
- **Permission Error (200)**: Missing pages_read_engagement → Log and disable → FATAL
- **Post Not Found (803)**: Skip → RECOVERABLE
- **Timeout**: Retry 3 times → RECOVERABLE

### 3. Twitter API v2 Integration

**Service**: `app/services/social_capture/twitter_service.py`

**Authentication**: Bearer Token (OAuth 2.0 App-Only)

**Endpoints Used**:
- `GET /2/users/:id/mentions` - Fetch mentions
- `GET /2/tweets/:id/liking_users` - Fetch users who liked
- `GET /2/dm_conversations/with/:participant_id/dm_events` - Fetch DMs (requires OAuth 1.0a)

**Rate Limits**:
- 75 requests per 15-minute window (mentions)
- Implement sliding window rate limiter

**Error Handling**:
- **Unauthorized (401)**: Invalid token → Disable polling, alert admin → FATAL
- **Rate Limit Exceeded (429)**: Wait for rate limit reset (header: x-rate-limit-reset) → RECOVERABLE
- **Forbidden (403)**: Account suspended or protected → Skip user → RECOVERABLE
- **Tweet Unavailable (404)**: Deleted or private → Skip → RECOVERABLE
- **Network Error**: Retry with exponential backoff → RECOVERABLE

### 4. LinkedIn API Integration

**Service**: `app/services/social_capture/linkedin_service.py`

**Authentication**: OAuth 2.0 Access Token (3-party authorization)

**Endpoints Used**:
- `GET /v2/shares` - Fetch organization posts
- `GET /v2/socialActions/{shareUrn}/comments` - Fetch comments
- `GET /v2/me/messages` - Fetch direct messages (restricted access)

**Rate Limits**:
- 500 requests per user per day
- Slower polling frequency (10 minutes)

**Error Handling**:
- **Unauthorized (401)**: Token expired → Refresh token flow → RECOVERABLE
- **Throttle (429)**: Exceeded daily quota → Pause until next day (00:00 UTC) → RECOVERABLE
- **Access Denied (403)**: Missing r_organization_social scope → FATAL
- **Resource Not Found (404)**: Share deleted → Skip → RECOVERABLE
- **Server Error (500)**: Retry with backoff → RECOVERABLE

---

## Email Reply Capture Architecture

### Option A: IMAP Polling (Gmail, Outlook)

**Service**: `app/services/inbound/email_imap_service.py`

**Implementation**:
- Connect via IMAP using OAuth2 tokens (Gmail) or app passwords
- Poll INBOX every 2 minutes
- Search for emails since last check: `SEARCH SINCE <date> UNSEEN`
- Parse email headers to extract thread IDs and match to outbound campaigns
- Extract email body (plain text and HTML)
- Mark as SEEN after processing

**Error Handling**:
- **Authentication Failed**: Token expired → Refresh OAuth token → RECOVERABLE
- **Connection Timeout**: Retry 3 times with 10s backoff → Log error at ERROR level → RECOVERABLE
- **IMAP Command Failed**: Log error, skip message → RECOVERABLE
- **Malformed Email**: Log at WARNING level, store raw in metadata → RECOVERABLE

### Option B: Webhook Integration (SendGrid, Mailgun)

**Service**: `app/services/inbound/email_webhook_service.py`

**Implementation**:
- Register webhook endpoint: `POST /api/v1/webhooks/inbound-email`
- Validate webhook signature (SendGrid: X-Twilio-Email-Event-Webhook-Signature)
- Parse inbound email payload
- Extract sender, subject, body, thread ID
- Store in `inbound_messages` table

**Webhook Validation**:
```python
def validate_sendgrid_webhook(request: Request) -> bool:
    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp")
    body = await request.body()
    
    expected_signature = hmac.new(
        settings.SENDGRID_WEBHOOK_SECRET.encode(),
        timestamp.encode() + body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f"sha256={expected_signature}")
```

**Error Handling**:
- **Invalid Signature**: Return 401, log at WARNING level → Non-recoverable (reject request)
- **Malformed Payload**: Return 400, log payload at ERROR level → Non-recoverable
- **Database Write Failure**: Return 500, log at CRITICAL level, trigger retry from provider → RECOVERABLE
- **Duplicate Message**: Return 200 (idempotent), log at DEBUG level → No action needed

**Recommended Approach**: Use **webhooks** for production (real-time, no polling overhead), fallback to **IMAP** for providers without webhook support.

---

## WhatsApp Business API Webhook Architecture

**Service**: `app/services/inbound/whatsapp_webhook_service.py`

**Endpoint**: `POST /api/v1/webhooks/whatsapp`

**Verification Endpoint**: `GET /api/v1/webhooks/whatsapp` (for Meta verification)

**Webhook Verification**:
```python
@router.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Invalid verification token")
```

**Message Processing**:
```python
@router.post("/webhooks/whatsapp")
async def handle_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.json()
    
    # Validate signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not validate_whatsapp_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Extract messages
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            
            for message in messages:
                # Store in inbound_messages
                await process_whatsapp_message(message, db)
    
    return {"status": "ok"}
```

**Signature Validation**:
```python
def validate_whatsapp_signature(payload: dict, signature: str) -> bool:
    expected_signature = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(),
        json.dumps(payload, separators=(",", ":")).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, f"sha256={expected_signature}")
```

**Error Handling**:
- **Invalid Signature**: Return 401 → Log at WARNING → FATAL (reject message)
- **Duplicate Message**: Check `platform_message_id` uniqueness → Return 200 → No action
- **Opt-Out Detected ("STOP")**: Add to suppression list → Return 200 → Log at INFO
- **Database Failure**: Return 500 → WhatsApp will retry → RECOVERABLE
- **Message Type Unsupported**: Return 200 (acknowledge) → Log at DEBUG → No action

---

## Celery Task Architecture and Scheduling

### Task Structure

All polling tasks follow the `DatabaseTask` base class pattern established in `app/workers/tasks.py`.

### 1. Social Media Polling Tasks

**File**: `app/workers/social_polling_tasks.py`

```python
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.social_polling_tasks.poll_instagram_engagements"
)
def poll_instagram_engagements(self):
    """Poll Instagram for new comments, DMs, and mentions every 5 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            InstagramService.fetch_and_store_engagements(db)
        )
        return {
            "status": "success",
            "platform": "INSTAGRAM",
            "engagements_found": result["count"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except RateLimitError as e:
        # Log and skip this iteration
        logger.warning(f"Instagram rate limit: {e}")
        return {"status": "rate_limited", "retry_after": e.retry_after}
    except AuthenticationError as e:
        # Disable integration
        logger.error(f"Instagram auth failed: {e}")
        return {"status": "auth_failed", "error": str(e)}
    finally:
        loop.close()
```

### 2. Email Reply Polling Task

```python
@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.workers.inbound_tasks.poll_email_replies"
)
def poll_email_replies(self):
    """Poll IMAP inbox for email replies every 2 minutes."""
    db = self.session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            EmailIMAPService.fetch_and_store_replies(db)
        )
        return {
            "status": "success",
            "replies_found": result["count"]
        }
    except IMAPConnectionError as e:
        logger.error(f"IMAP connection failed: {e}")
        return {"status": "connection_failed"}
    finally:
        loop.close()
```

### 3. Celery Beat Schedule

**File**: `backend/celeryconfig.py` (append to existing beat_schedule)

```python
celery_app.conf.beat_schedule.update({
    # Instagram polling - every 5 minutes
    'poll-instagram-engagements': {
        'task': 'app.workers.social_polling_tasks.poll_instagram_engagements',
        'schedule': 300.0,  # 5 minutes
        'options': {'expires': 240}
    },
    
    # Facebook polling - every 5 minutes
    'poll-facebook-engagements': {
        'task': 'app.workers.social_polling_tasks.poll_facebook_engagements',
        'schedule': 300.0,
        'options': {'expires': 240}
    },
    
    # Twitter polling - every 5 minutes
    'poll-twitter-mentions': {
        'task': 'app.workers.social_polling_tasks.poll_twitter_mentions',
        'schedule': 300.0,
        'options': {'expires': 240}
    },
    
    # LinkedIn polling - every 10 minutes (lower rate limits)
    'poll-linkedin-engagements': {
        'task': 'app.workers.social_polling_tasks.poll_linkedin_engagements',
        'schedule': 600.0,  # 10 minutes
        'options': {'expires': 540}
    },
    
    # Email reply polling - every 2 minutes
    'poll-email-replies': {
        'task': 'app.workers.inbound_tasks.poll_email_replies',
        'schedule': 120.0,  # 2 minutes
        'options': {'expires': 100}
    },
    
    # Process unprocessed social leads - every 3 minutes
    'process-social-leads': {
        'task': 'app.workers.social_processing_tasks.process_social_media_leads',
        'schedule': 180.0,
        'options': {'expires': 150}
    },
    
    # Process unprocessed inbound messages - every 2 minutes
    'process-inbound-messages': {
        'task': 'app.workers.inbound_tasks.process_inbound_messages',
        'schedule': 120.0,
        'options': {'expires': 100}
    }
})
```

### Task Concurrency and Resource Management

- **Worker Concurrency**: 4 workers (configurable)
- **Prefetch Multiplier**: 1 (sequential processing)
- **Task Time Limit**: 300 seconds (5 minutes per task)
- **Soft Time Limit**: 270 seconds
- **Max Retries**: 3 with exponential backoff

---

## Event Flow Integration

### New Events

Add to `WorkflowDefinition.trigger_type` valid values:

1. **SOCIAL_ENGAGEMENT_DETECTED**
2. **EMAIL_REPLY_RECEIVED**
3. **WHATSAPP_MESSAGE_RECEIVED**

### Event Emission Points

#### 1. Social Engagement Detected

**Trigger**: When a new high-interest social media engagement is captured

**Emitter**: `app/services/social_capture/social_processing_service.py`

```python
async def process_social_engagement(
    engagement: SocialMediaLead,
    db: Session
) -> BusinessLead:
    # Convert social engagement to business lead
    lead = await convert_social_to_lead(engagement, db)
    
    # Emit event
    await WorkflowEngineService.emit_event(
        event_type="SOCIAL_ENGAGEMENT_DETECTED",
        payload={
            "engagement_id": str(engagement.id),
            "lead_id": str(lead.id),
            "platform": engagement.platform,
            "username": engagement.social_username,
            "interest_score": engagement.interest_score,
            "message_preview": engagement.message_content[:200]
        },
        db=db
    )
    
    return lead
```

#### 2. Email Reply Received

**Trigger**: When an email reply is received and classified

**Emitter**: `app/services/inbound/email_processing_service.py`

```python
async def process_email_reply(
    message: InboundMessage,
    db: Session
) -> Dict[str, Any]:
    # Classify reply using AI
    classification = await ReplyIntelligenceService.classify_reply(
        message.message_body
    )
    
    message.classification = classification["classification"]
    message.sentiment = classification["sentiment"]
    message.suggested_reply = classification.get("suggested_reply")
    message.requires_human_attention = classification["requires_human_attention"]
    db.commit()
    
    # Emit event
    await WorkflowEngineService.emit_event(
        event_type="EMAIL_REPLY_RECEIVED",
        payload={
            "message_id": str(message.id),
            "sender": message.sender_contact,
            "classification": message.classification,
            "sentiment": message.sentiment,
            "campaign_id": str(message.campaign_id) if message.campaign_id else None
        },
        db=db
    )
    
    # Also emit REPLY_CLASSIFIED for existing workflow compatibility
    if message.classification in ["INTERESTED", "OBJECTION", "QUESTION"]:
        await WorkflowEngineService.emit_event(
            event_type="REPLY_CLASSIFIED",
            payload={
                "message_id": str(message.id),
                "classification": message.classification,
                "sender": message.sender_contact
            },
            db=db
        )
    
    return classification
```

#### 3. WhatsApp Message Received

**Trigger**: When a WhatsApp message is received

**Emitter**: `app/services/inbound/whatsapp_webhook_service.py`

```python
async def process_whatsapp_message(
    message_data: dict,
    db: Session
) -> InboundMessage:
    # Store message
    inbound_msg = InboundMessage(
        channel="WHATSAPP",
        sender_contact=message_data["from"],
        message_body=message_data["text"]["body"],
        platform_message_id=message_data["id"],
        received_at=datetime.utcnow(),
        metadata=message_data
    )
    db.add(inbound_msg)
    db.commit()
    
    # Emit event
    await WorkflowEngineService.emit_event(
        event_type="WHATSAPP_MESSAGE_RECEIVED",
        payload={
            "message_id": str(inbound_msg.id),
            "sender": inbound_msg.sender_contact,
            "message_preview": inbound_msg.message_body[:200]
        },
        db=db
    )
    
    return inbound_msg
```

### Event-Driven Workflow Examples

#### Workflow 1: Social Engagement to Lead

**Trigger**: `SOCIAL_ENGAGEMENT_DETECTED`

**Steps**:
1. Enrich social profile (fetch full profile data)
2. Research company from social profile
3. Calculate ICP score
4. Create CRM contact if qualified
5. Notify sales team if high-value

#### Workflow 2: Interested Reply to Task

**Trigger**: `EMAIL_REPLY_RECEIVED` (classification=INTERESTED)

**Steps**:
1. Create urgent CRM task
2. Log activity note
3. Pause follow-up sequence
4. Send Slack notification to sales rep

#### Workflow 3: WhatsApp Lead Capture

**Trigger**: `WHATSAPP_MESSAGE_RECEIVED`

**Steps**:
1. Classify message intent
2. Check if sender exists in CRM
3. Create or update lead
4. Send auto-acknowledgment (if not opt-out)

---

## Security Considerations

### 1. API Credential Management

**Storage**: Environment variables in `.env` (never committed to git)

**Required Secrets**:
```bash
# Instagram
INSTAGRAM_ACCESS_TOKEN=<long-lived-token>
INSTAGRAM_BUSINESS_ACCOUNT_ID=<account-id>

# Facebook
FACEBOOK_PAGE_ACCESS_TOKEN=<page-token>
FACEBOOK_PAGE_ID=<page-id>

# Twitter
TWITTER_BEARER_TOKEN=<bearer-token>
TWITTER_API_KEY=<api-key>
TWITTER_API_SECRET=<api-secret>

# LinkedIn
LINKEDIN_ACCESS_TOKEN=<oauth-token>
LINKEDIN_ORG_ID=<org-id>

# Email (SendGrid webhook)
SENDGRID_WEBHOOK_SECRET=<webhook-secret>

# WhatsApp
WHATSAPP_VERIFY_TOKEN=<verify-token>
WHATSAPP_APP_SECRET=<app-secret>
WHATSAPP_ACCESS_TOKEN=<access-token>
```

**Access Pattern**: All secrets loaded via `app/core/config.py` using Pydantic settings

**Rotation Strategy**: 
- Instagram/Facebook tokens: Refresh every 60 days
- Twitter tokens: No expiration (revoke and regenerate if compromised)
- LinkedIn tokens: Refresh every 60 days using refresh token flow
- Webhook secrets: Rotate quarterly

### 2. Webhook Validation

**All webhook endpoints MUST**:
- Validate HMAC signature before processing
- Use constant-time comparison (`hmac.compare_digest`)
- Return 401 for invalid signatures (do not process)
- Log validation failures at WARNING level
- Implement rate limiting (100 requests per minute per IP)

### 3. Rate Limiting

**Per-Platform Rate Limiters**:
- Use Redis-backed token bucket algorithm
- Track API calls per endpoint per time window
- Gracefully handle rate limit responses (429)
- Exponential backoff: 30s, 60s, 120s, 300s
- Log rate limit hits at WARNING level

**Implementation**:
```python
class SocialPlatformRateLimiter:
    def __init__(self, redis_client: Redis, platform: str, max_calls: int, window_seconds: int):
        self.redis = redis_client
        self.platform = platform
        self.max_calls = max_calls
        self.window_seconds = window_seconds
    
    async def acquire(self) -> bool:
        key = f"rate_limit:{self.platform}"
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, self.window_seconds)
        
        if current > self.max_calls:
            ttl = await self.redis.ttl(key)
            logger.warning(f"{self.platform} rate limit exceeded. Retry in {ttl}s")
            return False
        
        return True
```

### 4. Data Privacy (GDPR/CCPA Compliance)

**PII Handling**:
- Social usernames, emails, phone numbers are considered PII
- Store minimum necessary data
- Implement data retention policy (delete after 2 years if no activity)
- Support right to erasure (delete lead + all engagements)

**Consent Tracking**:
- Inbound messages imply consent (user initiated)
- Social engagements: public data, no consent required
- Do NOT send outbound messages to social leads without explicit consent

**Data Processing Agreement**:
- Document that social data is processed for legitimate business interest (B2B sales)
- Maintain audit log of all lead captures

### 5. Input Validation and Sanitization

**All user-generated content MUST**:
- Be sanitized before storage (strip HTML/scripts)
- Have max length limits enforced
- Be escaped before display in frontend
- Never be executed as code

**Validation Rules**:
- Email: RFC 5322 compliant
- Phone: E.164 format
- URLs: Valid protocol (https:// or http://)
- Message content: Max 5000 characters

---

## Implementation Phases

### Phase 1: Database Schema and Models (Week 1)

**Deliverables**:
1. Alembic migration `20261104_0001_multi_channel_lead_capture.py`
2. SQLAlchemy models:
   - `app/models/social_media_lead.py`
   - `app/models/inbound_message.py`
3. Update `app/models/business_lead.py` with new columns
4. Pydantic schemas:
   - `app/schemas/social_media_lead.py`
   - `app/schemas/inbound_message.py`

**Files to Create**:
```
backend/alembic/versions/20261104_0001_multi_channel_lead_capture.py
backend/app/models/social_media_lead.py
backend/app/models/inbound_message.py
backend/app/schemas/social_media_lead.py
backend/app/schemas/inbound_message.py
```

**Files to Modify**:
```
backend/app/models/business_lead.py (add lead_source column)
backend/app/models/__init__.py (import new models)
backend/app/schemas/__init__.py (import new schemas)
```

### Phase 2: Social Media Integration Services (Week 2-3)

**Deliverables**:
1. Instagram polling service
2. Facebook polling service
3. Twitter polling service
4. LinkedIn polling service
5. Social processing service (convert engagements to leads)
6. Rate limiter implementation

**Files to Create**:
```
backend/app/services/social_capture/__init__.py
backend/app/services/social_capture/instagram_service.py
backend/app/services/social_capture/facebook_service.py
backend/app/services/social_capture/twitter_service.py
backend/app/services/social_capture/linkedin_service.py
backend/app/services/social_capture/social_processing_service.py
backend/app/services/social_capture/rate_limiter.py
backend/app/services/social_capture/exceptions.py
```

**Dependencies**:
- `httpx` (async HTTP client)
- `tweepy` (Twitter API v2 wrapper)
- `python-linkedin-v2` (LinkedIn API wrapper)

### Phase 3: Email and WhatsApp Integration (Week 3-4)

**Deliverables**:
1. Email IMAP polling service
2. Email webhook service (SendGrid/Mailgun)
3. WhatsApp webhook service
4. Message processing and classification service

**Files to Create**:
```
backend/app/services/inbound/__init__.py
backend/app/services/inbound/email_imap_service.py
backend/app/services/inbound/email_webhook_service.py
backend/app/services/inbound/whatsapp_webhook_service.py
backend/app/services/inbound/message_processing_service.py
```

**Files to Modify**:
```
backend/app/api/v1/__init__.py (add webhook routes)
backend/app/api/v1/webhooks.py (create new file for webhook endpoints)
```

**Dependencies**:
- `imapclient` (IMAP client)
- `email` (Python standard library for email parsing)

### Phase 4: Celery Tasks and Scheduling (Week 4)

**Deliverables**:
1. Social polling tasks
2. Email polling tasks
3. Message processing tasks
4. Celery beat schedule updates

**Files to Create**:
```
backend/app/workers/social_polling_tasks.py
backend/app/workers/inbound_tasks.py
backend/app/workers/social_processing_tasks.py
```

**Files to Modify**:
```
backend/celeryconfig.py (add new beat schedules)
backend/app/workers/celery_app.py (import new tasks)
```

### Phase 5: Workflow Events and Automation (Week 5)

**Deliverables**:
1. New event types registered
2. Event emission in processing services
3. Default workflow definitions for:
   - Social engagement to lead
   - Interested email reply to task
   - WhatsApp lead capture
4. Event-driven qualification and routing

**Files to Modify**:
```
backend/app/services/social_capture/social_processing_service.py (emit events)
backend/app/services/inbound/message_processing_service.py (emit events)
backend/app/services/workflow_engine_service.py (register new event types)
```

**Database Seeds**:
```
backend/scripts/seed_social_workflows.py
```

### Phase 6: API Endpoints and Frontend Integration (Week 6)

**Deliverables**:
1. REST API endpoints:
   - `GET /api/v1/social-leads` (list social engagements)
   - `GET /api/v1/inbound-messages` (list inbound messages)
   - `POST /api/v1/social-leads/{id}/convert` (convert to lead)
   - `POST /api/v1/inbound-messages/{id}/reply` (send reply)
2. Frontend React components:
   - Social Leads Inbox
   - Inbound Messages Inbox
   - Lead conversion modal
3. Real-time notifications (WebSocket or polling)

**Files to Create**:
```
backend/app/api/v1/social_leads.py
backend/app/api/v1/inbound_messages.py
frontend/src/pages/SocialLeadsInbox.tsx
frontend/src/pages/InboundMessagesInbox.tsx
frontend/src/components/SocialLeadCard.tsx
frontend/src/components/InboundMessageCard.tsx
```

**Files to Modify**:
```
backend/app/api/v1/__init__.py (register new routers)
frontend/src/App.tsx (add new routes)
frontend/src/components/Sidebar.tsx (add navigation links)
```

---

## File Structure Summary

### Backend Structure

```
backend/
├── alembic/
│   └── versions/
│       └── 20261104_0001_multi_channel_lead_capture.py
├── app/
│   ├── models/
│   │   ├── social_media_lead.py (NEW)
│   │   ├── inbound_message.py (NEW)
│   │   └── business_lead.py (MODIFY: add lead_source)
│   ├── schemas/
│   │   ├── social_media_lead.py (NEW)
│   │   └── inbound_message.py (NEW)
│   ├── services/
│   │   ├── social_capture/ (NEW DIRECTORY)
│   │   │   ├── __init__.py
│   │   │   ├── instagram_service.py
│   │   │   ├── facebook_service.py
│   │   │   ├── twitter_service.py
│   │   │   ├── linkedin_service.py
│   │   │   ├── social_processing_service.py
│   │   │   ├── rate_limiter.py
│   │   │   └── exceptions.py
│   │   └── inbound/ (NEW DIRECTORY)
│   │       ├── __init__.py
│   │       ├── email_imap_service.py
│   │       ├── email_webhook_service.py
│   │       ├── whatsapp_webhook_service.py
│   │       └── message_processing_service.py
│   ├── api/
│   │   └── v1/
│   │       ├── social_leads.py (NEW)
│   │       ├── inbound_messages.py (NEW)
│   │       └── webhooks.py (NEW)
│   └── workers/
│       ├── social_polling_tasks.py (NEW)
│       ├── inbound_tasks.py (NEW)
│       └── social_processing_tasks.py (NEW)
└── celeryconfig.py (MODIFY: add beat schedules)
```

### Frontend Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── SocialLeadsInbox.tsx (NEW)
│   │   └── InboundMessagesInbox.tsx (NEW)
│   ├── components/
│   │   ├── SocialLeadCard.tsx (NEW)
│   │   ├── InboundMessageCard.tsx (NEW)
│   │   └── LeadConversionModal.tsx (NEW)
│   └── api/
│       ├── socialLeads.ts (NEW)
│       └── inboundMessages.ts (NEW)
```

---

## Testing Strategy

### Unit Tests

1. **Service Layer Tests**:
   - Mock API responses for each platform
   - Test rate limiting logic
   - Test error handling and retry logic
   - Test data transformation and validation

2. **Webhook Validation Tests**:
   - Valid signature → accept
   - Invalid signature → reject
   - Malformed payload → reject
   - Duplicate message → idempotent

### Integration Tests

1. **Database Tests**:
   - Create social_media_lead → verify storage
   - Create inbound_message → verify storage
   - Convert social engagement → verify lead creation
   - Test foreign key relationships

2. **Event Emission Tests**:
   - Emit SOCIAL_ENGAGEMENT_DETECTED → verify workflow triggered
   - Emit EMAIL_REPLY_RECEIVED → verify task created
   - Emit WHATSAPP_MESSAGE_RECEIVED → verify processing

### End-to-End Tests

1. **Social Platform Flow**:
   - Mock Instagram API → poll → store engagement → emit event → trigger workflow
2. **Email Reply Flow**:
   - Mock IMAP response → poll → classify → emit event → create task
3. **WhatsApp Flow**:
   - Mock webhook request → validate → store → emit event → auto-reply

---

## Monitoring and Observability

### Health Checks

1. **Platform Integration Health**:
   - Check last successful poll timestamp for each platform
   - Alert if no successful poll in last 30 minutes
   - Dashboard indicator: 🟢 Healthy / 🟡 Degraded / 🔴 Failed

2. **Webhook Health**:
   - Monitor webhook request rate
   - Track signature validation failure rate
   - Alert if validation failure rate > 5%

### Metrics to Track

1. **Engagement Metrics**:
   - Social engagements captured per platform per day
   - Email replies received per day
   - WhatsApp messages received per day
   - Conversion rate: social engagement → qualified lead

2. **System Metrics**:
   - API call count per platform per hour
   - Rate limit hits per platform per day
   - Task execution time (p50, p95, p99)
   - Task failure rate

3. **Data Quality Metrics**:
   - Duplicate message rate
   - Classification accuracy (requires human feedback)
   - Interest score distribution

### Logging Standards

**Log Levels**:
- **DEBUG**: API request/response details, message content
- **INFO**: Successful poll, engagement captured, lead created
- **WARNING**: Rate limit hit, validation failure, duplicate message
- **ERROR**: Authentication failure, API error, database error
- **CRITICAL**: Webhook endpoint down, Celery worker crash

**Structured Logging**:
```python
logger.info(
    "Social engagement captured",
    extra={
        "platform": "INSTAGRAM",
        "username": "@example_user",
        "engagement_type": "comment",
        "interest_score": 0.85,
        "engagement_id": str(engagement.id)
    }
)
```

---

## Risk Mitigation

### Risk 1: API Rate Limiting

**Impact**: Missed engagements, delayed lead capture

**Mitigation**:
- Implement strict rate limiters with safety margin (80% of limit)
- Exponential backoff on rate limit errors
- Alert when rate limit hit repeatedly
- Consider increasing polling interval dynamically

### Risk 2: Token Expiration

**Impact**: Integration stops working, no engagements captured

**Mitigation**:
- Implement token refresh flows for platforms that support it
- Monitor token expiration dates
- Alert 7 days before expiration
- Provide admin UI for easy token re-authorization

### Risk 3: Webhook Endpoint Downtime

**Impact**: Lost inbound messages

**Mitigation**:
- Implement health check endpoint
- Monitor webhook uptime (99.9% target)
- Fallback to IMAP polling if webhook fails repeatedly
- Platform retries (WhatsApp/SendGrid retry for 24-48 hours)

### Risk 4: High Volume Spam

**Impact**: Database bloat, processing overhead

**Mitigation**:
- Implement spam detection (keyword blocklist)
- Rate limit inbound messages per sender (max 10/hour)
- Auto-archive low-interest-score messages
- Periodic cleanup of processed messages > 90 days old

### Risk 5: PII Data Breach

**Impact**: GDPR violation, reputational damage

**Mitigation**:
- Encrypt sensitive fields at rest (social usernames, phone numbers)
- Implement row-level security in PostgreSQL
- Audit log all access to PII
- Regular security audits and penetration testing

---

## Performance Optimization

### Database Optimization

1. **Indexes**: All foreign keys, frequently queried columns, and timestamp columns
2. **Partitioning**: Consider partitioning `social_media_leads` and `inbound_messages` by month if volume exceeds 1M rows
3. **Archival**: Move processed records older than 90 days to cold storage table

### API Call Optimization

1. **Batch Requests**: Use batch endpoints where available (Instagram Media Insights)
2. **Incremental Polling**: Use `since` parameter to fetch only new data
3. **Parallel Requests**: Poll multiple platforms concurrently using asyncio
4. **Connection Pooling**: Reuse HTTP connections (httpx async client with connection pool)

### Task Optimization

1. **Task Chunking**: Process social leads in batches of 50
2. **Async Processing**: Use asyncio for I/O-bound operations
3. **Result Caching**: Cache platform API responses for 60 seconds (avoid duplicate calls)

---

## Codebase Patterns Reviewed

✅ **Database Patterns**:
- PostgreSQL with pgvector extension
- Alembic migrations with sequential numbering
- SQLAlchemy models with UUID primary keys
- Relationships with cascade delete

✅ **Celery Patterns**:
- `DatabaseTask` base class for session management
- Async/await with `asyncio.new_event_loop()`
- Beat schedule in `celeryconfig.py`
- Task expiration and timeout configuration

✅ **Service Patterns**:
- Static methods on service classes
- Async service methods
- Database session passed as parameter
- Error handling with try/except/finally

✅ **Event System**:
- `WorkflowEngineService.emit_event()` for event emission
- Event types as strings (NEW_LEAD, UNSUBSCRIBE, REPLY_CLASSIFIED)
- Payload as dictionary with lead/contact metadata

✅ **API Patterns**:
- FastAPI routers in `app/api/v1/`
- Pydantic schemas for request/response
- Dependency injection for database sessions
- HTTP exception handling

✅ **Configuration**:
- Pydantic settings in `app/core/config.py`
- Environment variables loaded from `.env`
- Optional API keys with fallback defaults
- Type-safe configuration access

---

## Conclusion

This design provides a comprehensive, production-ready architecture for multi-channel lead capture that:

1. **Integrates seamlessly** with the existing codebase patterns (Celery, PostgreSQL, event bus)
2. **Scales efficiently** with rate limiting, connection pooling, and async processing
3. **Handles errors gracefully** with specific recovery strategies for each failure mode
4. **Maintains security** with webhook validation, secret management, and PII protection
5. **Enables automation** through event-driven workflows triggered by social and messaging events
6. **Supports testability** with clear service boundaries and mockable dependencies

The phased implementation plan ensures incremental delivery with minimal risk, allowing validation at each stage before proceeding to the next.

---

**Document Version**: 1.0  
**Last Updated**: 2026-11-04  
**Author**: AI System Designer  
**Review Status**: Ready for Implementation
