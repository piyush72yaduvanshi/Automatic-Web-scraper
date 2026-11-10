# CRM System Production Optimization - Implementation Plan

**Generated:** 2024-01-XX  
**Based on:** Investigation Report (d:\MVP\.agents\tasks\crm-audit\analysis\investigation-report.md)  
**Execution Model:** Sequential FEAT implementation with convergence loop

---

## Overview

This implementation plan addresses the critical gaps identified in the investigation report to bring the CRM system to production-ready status. The plan is organized into 5 prioritized features (FEATs) covering database performance, API rate limiting, frontend caching, security hardening, and monitoring.

**Total Estimated Time:** 8-10 working days  
**Approach:** Incremental implementation with verification after each feature

---

## Feature Summary

| FEAT | Type | Description | Priority | Estimated Effort |
|------|------|-------------|----------|-----------------|
| FEAT-001 | perf | Database performance indexes | P0 Critical | 1 day |
| FEAT-002 | feat | API rate limiting | P0 Critical | 1.5 days |
| FEAT-003 | feat | Frontend API caching with React Query | P1 High | 2 days |
| FEAT-004 | feat | Security hardening (CORS, secrets, headers) | P0 Critical | 1.5 days |
| FEAT-005 | feat | Monitoring & observability (Sentry, logs, health) | P1 High | 2 days |

---

## FEAT-001: Database Performance Optimization ⚡

### Objective
Add missing database indexes to prevent performance degradation at scale. Current investigation found zero indexes on frequently queried columns, which will cause full table scans as data grows.

### Changes Required

#### Files to Modify:
1. **NEW:** `backend/alembic/versions/YYYYMMDD_HHMMSS_add_performance_indexes.py`
2. **NEW:** `backend/docs/DATABASE_INDEXES.md`

### Implementation Steps

#### 1. Create Alembic Migration
```bash
cd backend
alembic revision -m "add_performance_indexes"
```

Edit the generated migration file with these indexes:

```python
def upgrade():
    # Business Leads - Most queried table
    op.create_index('idx_business_leads_status', 'business_leads', ['status'])
    op.create_index('idx_business_leads_source_provider', 'business_leads', ['source_provider'])
    op.create_index('idx_business_leads_qualification_score', 'business_leads', ['qualification_score'])
    op.create_index('idx_business_leads_created_at', 'business_leads', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})
    
    # CRM Core
    op.create_index('idx_companies_status', 'companies', ['status'])
    op.create_index('idx_deals_status', 'deals', ['status'])
    op.create_index('idx_deals_stage_id', 'deals', ['stage_id'])
    op.create_index('idx_contacts_company_id', 'contacts', ['company_id'])
    op.create_index('idx_activities_company_id', 'activities', ['company_id'])
    
    # Discovery System
    op.create_index('idx_discovery_jobs_status', 'discovery_jobs', ['status'])
    op.create_index('idx_discovery_jobs_created_at', 'discovery_jobs', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})
    
    # Outreach
    op.create_index('idx_outreach_approvals_status', 'outreach_approvals', ['status'])
    op.create_index('idx_conversations_status', 'conversations', ['status'])
    op.create_index('idx_conversations_last_message_at', 'conversations', ['last_message_at'], postgresql_using='btree', postgresql_ops={'last_message_at': 'DESC'})
    
    # pgvector Semantic Search - CRITICAL for RAG performance
    op.execute("""
        CREATE INDEX idx_knowledge_chunks_embedding 
        ON knowledge_chunks 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)

def downgrade():
    op.drop_index('idx_business_leads_status')
    op.drop_index('idx_business_leads_source_provider')
    op.drop_index('idx_business_leads_qualification_score')
    op.drop_index('idx_business_leads_created_at')
    op.drop_index('idx_companies_status')
    op.drop_index('idx_deals_status')
    op.drop_index('idx_deals_stage_id')
    op.drop_index('idx_contacts_company_id')
    op.drop_index('idx_activities_company_id')
    op.drop_index('idx_discovery_jobs_status')
    op.drop_index('idx_discovery_jobs_created_at')
    op.drop_index('idx_outreach_approvals_status')
    op.drop_index('idx_conversations_status')
    op.drop_index('idx_conversations_last_message_at')
    op.drop_index('idx_knowledge_chunks_embedding')
```

#### 2. Apply Migration
```bash
cd backend
alembic upgrade head
```

#### 3. Verify Index Creation
```bash
docker exec -it crm_leads_postgres psql -U postgres -d crm_leads -c "\\d+ business_leads"
```

Expected output should show indexes section with new indexes listed.

#### 4. Test Query Performance
```sql
EXPLAIN ANALYZE SELECT * FROM business_leads WHERE status = 'qualified';
```

Should show "Index Scan using idx_business_leads_status" instead of "Seq Scan".

### Verification Checklist
- [ ] Migration file created successfully
- [ ] `alembic upgrade head` completes without errors
- [ ] All 15 indexes visible in database schema
- [ ] EXPLAIN ANALYZE shows index usage
- [ ] `alembic downgrade -1` successfully removes indexes
- [ ] `pytest tests/ -v` passes all existing tests

### Risk Assessment
**Low Risk** - Additive change, no data modification, fully reversible

---

## FEAT-002: API Rate Limiting 🛡️

### Objective
Protect API from abuse and prevent quota exhaustion on external providers (Apify, Gemini, OpenRouter). Current system has no rate limiting, making it vulnerable to DoS attacks and runaway costs.

### Changes Required

#### Files to Modify:
1. `backend/requirements.txt` - Add slowapi==0.1.9
2. **NEW:** `backend/app/core/rate_limiter.py`
3. `backend/app/core/config.py` - Add rate limit settings
4. `backend/main.py` - Add rate limiter middleware
5. `backend/app/api/v1/discovery.py` - Add rate limit decorators
6. `backend/app/api/v1/agents.py` - Add rate limit decorators
7. `backend/app/api/v1/outreach.py` - Add rate limit decorators
8. **NEW:** `backend/tests/test_rate_limiting.py`
9. **NEW:** `backend/docs/API_RATE_LIMITS.md`

### Implementation Steps

#### 1. Add Dependencies
```txt
# Add to backend/requirements.txt
slowapi==0.1.9
limits==3.7.0
```

Run: `pip install -r backend/requirements.txt`

#### 2. Create Rate Limiter Module
**File:** `backend/app/core/rate_limiter.py`

```python
"""Rate limiting using Redis backend."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Create limiter with Redis storage for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.REDIS_URL),
    strategy="fixed-window",
)
```

#### 3. Add Configuration
**File:** `backend/app/core/config.py`

Add these fields to Settings class:
```python
# Rate Limiting Configuration
RATE_LIMIT_DISCOVERY: str = "10/minute"
RATE_LIMIT_AI_AGENTS: str = "20/minute"
RATE_LIMIT_OUTREACH: str = "10/minute"
RATE_LIMIT_DEFAULT: str = "60/minute"
```

#### 4. Integrate Middleware
**File:** `backend/main.py`

```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

#### 5. Apply to Discovery Endpoints
**File:** `backend/app/api/v1/discovery.py`

```python
from app.core.rate_limiter import limiter
from app.core.config import settings

@router.post("/jobs", response_model=DiscoveryJobResponse)
@limiter.limit(settings.RATE_LIMIT_DISCOVERY)
async def create_discovery_job(request: Request, ...):
    # existing code
```

Apply to: `create_discovery_job`, `stream_discovery_scan`, `quick_scan`

#### 6. Apply to AI Agent Endpoints
**File:** `backend/app/api/v1/agents.py`

Apply `@limiter.limit(settings.RATE_LIMIT_AI_AGENTS)` to agent execution endpoints.

#### 7. Apply to Outreach Endpoints
**File:** `backend/app/api/v1/outreach.py`

Apply `@limiter.limit(settings.RATE_LIMIT_OUTREACH)` to approval and send endpoints.

#### 8. Create Tests
**File:** `backend/tests/test_rate_limiting.py`

```python
"""Test rate limiting functionality."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_rate_limit_discovery_endpoint():
    """Test discovery endpoint rate limit."""
    # Make 11 requests rapidly
    for i in range(11):
        response = client.post("/api/v1/discovery/jobs", json={
            "query": "test",
            "location": "test",
        })
        if i < 10:
            assert response.status_code in [200, 422]  # Success or validation error
        else:
            assert response.status_code == 429  # Rate limit exceeded
            assert "Retry-After" in response.headers

def test_rate_limit_per_endpoint():
    """Test different limits for different endpoints."""
    # Discovery: 10/min
    # Agents: 20/min
    # Verify independent counters
```

### Verification Checklist
- [ ] slowapi installed successfully
- [ ] Rate limiter middleware active (check logs on startup)
- [ ] Discovery endpoint returns 429 after 10 requests/minute
- [ ] Agent endpoint returns 429 after 20 requests/minute
- [ ] Retry-After header present in 429 responses
- [ ] Redis stores rate limit state (check `KEYS '*rate*'`)
- [ ] All new tests pass

### Risk Assessment
**Low Risk** - Middleware-level change, can be disabled via config if issues arise

---

## FEAT-003: Frontend API Caching with TanStack Query ⚡

### Objective
Eliminate redundant API calls, improve perceived performance, and implement proper loading/error states. Current frontend makes repeated identical requests without caching.

### Changes Required

#### Files to Modify:
1. `frontend/package.json` - Add @tanstack/react-query
2. **NEW:** `frontend/src/services/queryClient.ts`
3. `frontend/src/main.tsx` - Wrap with QueryClientProvider
4. `frontend/src/hooks/useLeads.ts` - Refactor to use React Query
5. `frontend/src/hooks/useJobs.ts` - Refactor to use React Query
6. `frontend/src/hooks/useStats.ts` - Refactor to use React Query
7. **NEW:** `frontend/src/hooks/useCompanies.ts`
8. **NEW:** `frontend/src/hooks/useContacts.ts`
9. **NEW:** `frontend/src/hooks/useDeals.ts`
10. `frontend/src/pages/Discovery.tsx` - Use query hooks
11. `frontend/src/pages/DealsPipeline.tsx` - Add optimistic updates
12. **NEW:** `frontend/src/components/ErrorBoundary.tsx`

### Implementation Steps

#### 1. Install Dependencies
```bash
cd frontend
npm install @tanstack/react-query@5.17.19 @tanstack/react-query-devtools@5.17.19
```

#### 2. Create Query Client
**File:** `frontend/src/services/queryClient.ts`

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 2,
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

#### 3. Wrap App
**File:** `frontend/src/main.tsx`

```typescript
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './services/queryClient';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
);
```

#### 4. Refactor useLeads Hook
**File:** `frontend/src/hooks/useLeads.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { BusinessLead, PaginatedResponse } from '../types';

export const useLeads = (page: number = 1, pageSize: number = 20) => {
  return useQuery<PaginatedResponse<BusinessLead>>({
    queryKey: ['leads', page, pageSize],
    queryFn: async () => {
      const response = await api.get('/leads', {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
  });
};

export const useLeadDetail = (id: string) => {
  return useQuery<BusinessLead>({
    queryKey: ['lead', id],
    queryFn: async () => {
      const response = await api.get(`/leads/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateLead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<BusinessLead>) => {
      const response = await api.post('/leads', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
    },
  });
};
```

#### 5. Refactor useJobs Hook
**File:** `frontend/src/hooks/useJobs.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { DiscoveryJob, PaginatedResponse } from '../types';

export const useJobs = (page: number = 1, pageSize: number = 20) => {
  return useQuery<PaginatedResponse<DiscoveryJob>>({
    queryKey: ['jobs', page, pageSize],
    queryFn: async () => {
      const response = await api.get('/discovery/jobs', {
        params: { page, page_size: pageSize },
      });
      return response.data;
    },
    refetchInterval: (data) => {
      // Auto-refresh every 10 seconds if any jobs are running
      const hasRunning = data?.items.some(job => job.status === 'RUNNING');
      return hasRunning ? 10000 : false;
    },
  });
};
```

#### 6. Refactor useStats Hook
**File:** `frontend/src/hooks/useStats.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Stats } from '../types';

export const useStats = () => {
  return useQuery<Stats>({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await api.get('/stats');
      return response.data;
    },
    staleTime: 30 * 1000, // 30 seconds
  });
};
```

#### 7. Create Additional Hooks
Create `useCompanies.ts`, `useContacts.ts`, `useDeals.ts` following the same pattern.

#### 8. Update Discovery Page
**File:** `frontend/src/pages/Discovery.tsx`

Replace direct API calls with `useJobs()` and `useCreateJob()` hooks.

#### 9. Add Optimistic Updates to Pipeline
**File:** `frontend/src/pages/DealsPipeline.tsx`

```typescript
const updateDealMutation = useMutation({
  mutationFn: async ({ dealId, stageId }: { dealId: string; stageId: string }) => {
    const response = await api.patch(`/crm/deals/${dealId}`, { stage_id: stageId });
    return response.data;
  },
  onMutate: async (variables) => {
    // Cancel outgoing queries
    await queryClient.cancelQueries({ queryKey: ['deals'] });
    
    // Snapshot previous value
    const previousDeals = queryClient.getQueryData(['deals']);
    
    // Optimistically update
    queryClient.setQueryData(['deals'], (old: any) => {
      // ... update logic
    });
    
    return { previousDeals };
  },
  onError: (err, variables, context) => {
    // Rollback on error
    queryClient.setQueryData(['deals'], context?.previousDeals);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['deals'] });
  },
});
```

#### 10. Create Error Boundary
**File:** `frontend/src/components/ErrorBoundary.tsx`

```typescript
import React from 'react';

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div className="error-fallback">Something went wrong. Please refresh.</div>;
    }
    return this.props.children;
  }
}
```

### Verification Checklist
- [ ] React Query installed and DevTools visible
- [ ] Network tab shows single request for repeated page visits (cache working)
- [ ] Jobs page auto-refreshes every 10 seconds when jobs running
- [ ] Deal drag-and-drop shows immediate UI update (optimistic)
- [ ] Error states handled gracefully
- [ ] No TypeScript compilation errors
- [ ] No console errors in browser

### Risk Assessment
**Medium Risk** - Major refactor of data fetching, requires thorough testing

---

## FEAT-004: Security Hardening 🔒

### Objective
Remove hardcoded secrets, add security headers, harden CORS, and set resource limits. Current configuration is insecure for production deployment.

### Changes Required

#### Files to Modify:
1. `docker-compose.yml` - Remove hardcoded credentials, add resource limits
2. `backend/app/core/config.py` - Harden CORS for production
3. **NEW:** `backend/app/core/security.py`
4. `backend/main.py` - Add security headers middleware
5. **NEW:** `backend/.env.example`
6. **NEW:** `frontend/.env.example`
7. `backend/README.md` - Document secrets management
8. **NEW:** `backend/tests/test_security_hardening.py`

### Implementation Steps

#### 1. Update Docker Compose - Remove Hardcoded Secrets
**File:** `docker-compose.yml`

```yaml
services:
  postgres:
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_me_in_production}  # Changed
      POSTGRES_DB: crm_leads

  minio:
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}  # Already using env var
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-change_me_minio_password}  # Changed default
```

#### 2. Add Resource Limits
**File:** `docker-compose.yml`

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          memory: 256M
    restart: unless-stopped  # Add to all services

  celery_worker:
    deploy:
      resources:
        limits:
          memory: 256M

  frontend:
    deploy:
      resources:
        limits:
          memory: 256M

  postgres:
    deploy:
      resources:
        limits:
          memory: 1G

  redis:
    deploy:
      resources:
        limits:
          memory: 256M
```

#### 3. Harden CORS Configuration
**File:** `backend/app/core/config.py`

```python
@field_validator("ALLOWED_ORIGINS", mode="before")
@classmethod
def parse_and_validate_origins(cls, v):
    if isinstance(v, str):
        origins = [i.strip() for i in v.split(",") if i.strip()]
    else:
        origins = v
    
    # In production, reject overly permissive origins
    if os.getenv("APP_ENV") == "production":
        for origin in origins:
            if "*" in origin and origin != "*":
                raise ValueError(f"Wildcard origins not allowed in production: {origin}")
    
    return origins
```

**File:** `backend/main.py`

```python
# Update CORS middleware - remove overly permissive regex in production
if settings.APP_ENV == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,  # Exact match only
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)...",  # Dev only
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

#### 4. Create Security Headers Middleware
**File:** `backend/app/core/security.py`

```python
"""Security headers middleware."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
```

#### 5. Add Middleware to App
**File:** `backend/main.py`

```python
from app.core.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

#### 6. Create .env.example Files
**File:** `backend/.env.example`

```bash
# Application Configuration
APP_NAME="AI Sales & CRM Operating System"
APP_ENV=development  # development | staging | production
DEBUG=true

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173

# Database
DATABASE_URL=postgresql+psycopg://postgres:CHANGE_THIS_PASSWORD@localhost:5432/crm_leads

# Redis
REDIS_URL=redis://:CHANGE_THIS_PASSWORD@localhost:6379/0

# MinIO Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=CHANGE_THIS_ACCESS_KEY
MINIO_SECRET_KEY=CHANGE_THIS_SECRET_KEY

# API Keys (Required for full functionality)
APIFY_API_TOKEN=your_apify_token_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Security
SECRET_KEY=CHANGE_THIS_SECRET_KEY_MINIMUM_32_CHARS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Monitoring (Optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

**File:** `frontend/.env.example`

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000/api/v1

# Monitoring (Optional)
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

#### 7. Update README
**File:** `backend/README.md`

Add section:

```markdown
## Secrets Management

### Development
1. Copy `.env.example` to `.env`
2. Fill in required API keys
3. Never commit `.env` to git

### Production
Use environment-specific secrets management:
- **AWS:** AWS Secrets Manager or Parameter Store
- **Azure:** Azure Key Vault
- **GCP:** Secret Manager
- **Docker:** Docker secrets
- **Kubernetes:** Kubernetes secrets

Set environment variables in production environment, do not use .env files.
```

#### 8. Create Security Tests
**File:** `backend/tests/test_security_hardening.py`

```python
"""Test security hardening."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_security_headers_present():
    """Test all security headers are added."""
    response = client.get("/api/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers

def test_cors_production_mode(monkeypatch):
    """Test CORS rejects unauthorized origins in production."""
    monkeypatch.setenv("APP_ENV", "production")
    # Test CORS behavior
```

### Verification Checklist
- [ ] No hardcoded passwords in docker-compose.yml
- [ ] Resource limits applied to all containers (`docker stats` shows limits)
- [ ] Security headers present in all responses
- [ ] CORS rejects unauthorized origins in production mode
- [ ] .env.example files created with documentation
- [ ] README.md documents secrets management
- [ ] All security tests pass

### Risk Assessment
**Low Risk** - Configuration changes, fully testable, reversible

---

## FEAT-005: Monitoring & Observability 📊

### Objective
Add error tracking, structured logging, health monitoring, and metrics collection. Current system has zero observability, making production incidents difficult to diagnose.

### Changes Required

#### Files to Modify:
1. `backend/requirements.txt` - Add Sentry and Prometheus instrumentation
2. `frontend/package.json` - Add Sentry React SDK
3. **NEW:** `backend/app/core/monitoring.py`
4. `backend/main.py` - Initialize Sentry and request ID middleware
5. `frontend/src/main.tsx` - Initialize Sentry
6. **NEW:** `backend/app/api/v1/monitoring.py`
7. **NEW:** `frontend/src/pages/MonitoringDashboard.tsx`
8. `frontend/src/App.tsx` - Add monitoring route
9. **NEW:** `backend/tests/test_monitoring.py`

### Implementation Steps

#### 1. Add Backend Dependencies
```txt
# Add to backend/requirements.txt
sentry-sdk[fastapi]==1.39.2
prometheus-fastapi-instrumentator==6.1.0
```

Run: `pip install -r backend/requirements.txt`

#### 2. Add Frontend Dependencies
```bash
cd frontend
npm install @sentry/react@7.99.0
```

#### 3. Create Monitoring Module
**File:** `backend/app/core/monitoring.py`

```python
"""Monitoring and observability configuration."""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings

def initialize_sentry():
    """Initialize Sentry error tracking if DSN is configured."""
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=settings.APP_ENV,
            traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
        )
        return True
    return False
```

#### 4. Initialize Monitoring in Backend
**File:** `backend/main.py`

```python
import uuid
from app.core.monitoring import initialize_sentry
from prometheus_fastapi_instrumentator import Instrumentator

# Initialize Sentry
sentry_enabled = initialize_sentry()
if sentry_enabled:
    logger.info("Sentry error tracking initialized")

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

#### 5. Update Logging Configuration
**File:** `backend/main.py`

```python
import logging
import json

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, 'request_id', 'N/A')
        return True

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "request_id": "%(request_id)s", "module": "%(name)s", "message": "%(message)s"}',
)

for handler in logging.root.handlers:
    handler.addFilter(RequestIDFilter())
```

#### 6. Initialize Sentry in Frontend
**File:** `frontend/src/main.tsx`

```typescript
import * as Sentry from '@sentry/react';

const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    integrations: [
      new Sentry.BrowserTracing(),
      new Sentry.Replay(),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}
```

#### 7. Create Health Check Endpoint
**File:** `backend/app/api/v1/monitoring.py`

```python
"""Monitoring and health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.storage_service import StorageService
import redis

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check for all dependencies."""
    health = {
        "overall": "healthy",
        "postgres": "unknown",
        "redis": "unknown",
        "minio": "unknown",
    }
    
    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        health["postgres"] = "healthy"
    except Exception as e:
        health["postgres"] = "unhealthy"
        health["overall"] = "degraded"
    
    # Check Redis
    try:
        from app.core.config import settings
        r = redis.from_url(str(settings.REDIS_URL))
        r.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = "unhealthy"
        health["overall"] = "degraded"
    
    # Check MinIO
    if StorageService.health_check():
        health["minio"] = "healthy"
    else:
        health["minio"] = "degraded"
        health["overall"] = "degraded"
    
    return health
```

Add to `backend/app/api/v1/__init__.py`:
```python
from app.api.v1 import monitoring
api_router.include_router(monitoring.router)
```

#### 8. Create Monitoring Dashboard Page
**File:** `frontend/src/pages/MonitoringDashboard.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Activity, Database, Server, HardDrive, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import api from '../services/api';

export const MonitoringDashboard: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await api.get('/monitoring/health');
        setHealth(response.data);
      } catch (error) {
        console.error('Health check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    if (status === 'healthy') return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (status === 'degraded') return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    return <XCircle className="w-5 h-5 text-red-500" />;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Activity className="w-7 h-7 text-indigo-500" />
        <h1 className="text-2xl font-bold text-white">System Health Monitoring</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Overall Status */}
        <div className="bg-[#0A0F1E] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Overall</span>
            {health && getStatusIcon(health.overall)}
          </div>
          <p className="text-xl font-semibold text-white capitalize">{health?.overall || 'Loading...'}</p>
        </div>

        {/* PostgreSQL */}
        <div className="bg-[#0A0F1E] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">PostgreSQL</span>
            {health && getStatusIcon(health.postgres)}
          </div>
          <p className="text-xl font-semibold text-white capitalize">{health?.postgres || 'Loading...'}</p>
        </div>

        {/* Redis */}
        <div className="bg-[#0A0F1E] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">Redis</span>
            {health && getStatusIcon(health.redis)}
          </div>
          <p className="text-xl font-semibold text-white capitalize">{health?.redis || 'Loading...'}</p>
        </div>

        {/* MinIO */}
        <div className="bg-[#0A0F1E] border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">MinIO S3</span>
            {health && getStatusIcon(health.minio)}
          </div>
          <p className="text-xl font-semibold text-white capitalize">{health?.minio || 'Loading...'}</p>
        </div>
      </div>

      {/* Metrics Link */}
      <div className="mt-6 bg-[#0A0F1E] border border-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-white mb-3">Prometheus Metrics</h2>
        <a
          href="http://localhost:8000/metrics"
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-400 hover:text-indigo-300 text-sm"
        >
          View raw Prometheus metrics →
        </a>
      </div>
    </div>
  );
};
```

#### 9. Add Monitoring Route
**File:** `frontend/src/App.tsx`

```typescript
const MonitoringDashboard = lazy(() => 
  import('./pages/MonitoringDashboard').then(m => ({ default: m.MonitoringDashboard }))
);

// In Routes
<Route path="monitoring" element={<MonitoringDashboard />} />
```

#### 10. Create Monitoring Tests
**File:** `backend/tests/test_monitoring.py`

```python
"""Test monitoring endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint_returns_status():
    """Test health endpoint returns system status."""
    response = client.get("/api/v1/monitoring/health")
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert "postgres" in data
    assert "redis" in data
    assert "minio" in data

def test_metrics_endpoint_prometheus_format():
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text or "fastapi" in response.text

def test_request_id_header_present():
    """Test X-Request-ID header added to responses."""
    response = client.get("/api/v1/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # UUID length
```

### Verification Checklist
- [ ] Sentry SDK installed in backend and frontend
- [ ] Backend starts successfully (with or without SENTRY_DSN)
- [ ] Request IDs present in all responses (X-Request-ID header)
- [ ] Request IDs visible in backend logs
- [ ] GET /api/v1/monitoring/health returns detailed status
- [ ] GET /metrics returns Prometheus metrics
- [ ] Frontend /monitoring page displays health dashboard
- [ ] Health dashboard auto-refreshes every 30 seconds
- [ ] All monitoring tests pass

### Risk Assessment
**Low Risk** - Additive feature, no impact on existing functionality

---

## Convergence & Integration Verification

After all 5 FEATs are implemented, perform end-to-end integration testing:

### Integration Test Checklist
- [ ] Start all services: `docker compose up -d`
- [ ] Run migrations: `cd backend && alembic upgrade head`
- [ ] Start backend: `cd backend && python main.py`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Access frontend: http://localhost:5173
- [ ] Check monitoring dashboard: http://localhost:5173/monitoring (all services healthy)
- [ ] Test discovery: Create discovery job, verify rate limiting after 10 requests
- [ ] Test caching: Navigate between pages, verify instant loads (React Query DevTools)
- [ ] Test security headers: `curl -I http://localhost:8000/api/v1/health` (X-Frame-Options present)
- [ ] Test database performance: Run discovery job, check query times are acceptable
- [ ] Run full test suite: `cd backend && pytest tests/ -v` (all tests pass)
- [ ] Check Prometheus metrics: http://localhost:8000/metrics (metrics exposed)
- [ ] Verify resource limits: `docker stats` (shows limits on containers)
- [ ] Test error tracking: Trigger error, verify logged/sent to Sentry (if configured)

---

## Post-Implementation Documentation Updates

### Files to Update:
1. `README.md` - Add monitoring, rate limiting, caching sections
2. `docs/DEPLOYMENT.md` - Update with security hardening steps
3. `docs/TROUBLESHOOTING.md` - Add common issues and solutions
4. `docs/PERFORMANCE.md` - Document indexes, caching strategy

---

## Success Criteria

This implementation is considered complete when:

1. ✅ All 5 FEATs have `status: "completed"` in their JSON files
2. ✅ All integration tests pass
3. ✅ System can run end-to-end with discovery, enrichment, and AI agents functional
4. ✅ Monitoring dashboard shows all services healthy
5. ✅ Rate limiting prevents API abuse
6. ✅ Database queries use indexes (verified via EXPLAIN ANALYZE)
7. ✅ Frontend caching reduces redundant network requests
8. ✅ Security headers present on all responses
9. ✅ No hardcoded secrets in docker-compose.yml
10. ✅ Documentation updated with new features

---

## Risk Mitigation

### Rollback Plan
Each FEAT is independently reversible:
- **FEAT-001:** `alembic downgrade -1` removes indexes
- **FEAT-002:** Disable rate limiter in config
- **FEAT-003:** Remove QueryClientProvider wrapping (revert to direct API calls)
- **FEAT-004:** Revert docker-compose.yml and config.py changes
- **FEAT-005:** Remove Sentry initialization

### Testing Strategy
- Unit tests for each feature
- Integration tests after each FEAT
- Full regression testing in convergence phase

### Communication Plan
- Document all changes in CHANGELOG.md
- Update team on security hardening requirements
- Provide .env.example setup instructions

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| FEAT-001 (Database Indexes) | 1 day | None |
| FEAT-002 (Rate Limiting) | 1.5 days | Redis running |
| FEAT-003 (React Query) | 2 days | FEAT-002 (for testing) |
| FEAT-004 (Security) | 1.5 days | None |
| FEAT-005 (Monitoring) | 2 days | All services running |
| Integration & Testing | 1 day | All FEATs complete |
| **Total** | **9 days** | |

---

**Plan End** | Ready for Implementation
