# CRM System - Production Deployment Guide

**Version:** 2.5.0  
**Last Updated:** November 10, 2026  
**Target Environment:** Production  
**Deployment Status:** Ready for Production

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Docker Deployment](#docker-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Monitoring Setup](#monitoring-setup)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)
10. [Maintenance Operations](#maintenance-operations)

---

## Prerequisites

### System Requirements

**Hardware (Minimum):**
- CPU: 2 cores (4 recommended)
- RAM: 4GB (8GB recommended)
- Disk: 20GB free space (50GB recommended)
- Network: Stable internet connection

**Software:**
- Docker: 24.0.0+ with Compose V2
- Git: 2.40.0+
- Operating System: Linux (Ubuntu 22.04+), macOS 12+, or Windows 10+ with WSL2

**Network Requirements:**
- Outbound HTTPS (443) for API providers
- Inbound HTTP/HTTPS for user access
- Domain name (optional but recommended)

---

### API Keys Required

Obtain the following API keys before deployment:

**Critical (Required):**
- `APIFY_API_TOKEN` - Lead discovery (https://console.apify.com/)
- `GEMINI_API_KEY` - AI agents (https://makersuite.google.com/app/apikey)
- `POSTGRES_PASSWORD` - Database security

**Optional (Enhanced Functionality):**
- `OPENROUTER_API_KEY` - AI fallback (https://openrouter.ai/)
- `GOOGLE_PLACES_API_KEY` - Discovery fallback (https://console.cloud.google.com/)
- `FIRECRAWL_API_KEY` - Website enrichment (https://firecrawl.dev/)
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` - Email outreach
- `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` - WhatsApp messaging
- `SENTRY_DSN` - Error tracking (https://sentry.io/)

---

## Pre-Deployment Checklist

### Code Preparation

- [ ] Clone repository to production server
- [ ] Checkout production branch (main)
- [ ] Verify commit: `9d086c0` or later
- [ ] Review recent changes: `git log --oneline -10`

### Configuration Files

- [ ] Create `.env` file from `.env.example`
- [ ] Set all required environment variables
- [ ] Generate secure `SECRET_KEY` (32+ characters)
- [ ] Configure production `ALLOWED_ORIGINS`
- [ ] Set strong database passwords

### Infrastructure

- [ ] Docker and Docker Compose installed
- [ ] Sufficient disk space available (50GB+)
- [ ] Network ports available (8000, 3000, 5432, 6379, 9000)
- [ ] Firewall rules configured
- [ ] SSL certificates obtained (if using HTTPS)

---

## Environment Configuration

### 1. Create Environment File

Copy the example file:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Backend Configuration

Edit `backend/.env`:

```bash
# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_NAME="AI Sales & CRM Operating System"
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# ============================================================
# SERVER CONFIGURATION
# ============================================================

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=https://your-domain.com

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

# IMPORTANT: Generate a strong password
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD_HERE>
DATABASE_URL=postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@postgres:5432/crm_leads
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ============================================================
# REDIS CONFIGURATION
# ============================================================

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ============================================================
# MINIO OBJECT STORAGE
# ============================================================

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<GENERATE_ACCESS_KEY>
MINIO_SECRET_KEY=<GENERATE_SECRET_KEY_32_CHARS>
MINIO_BUCKET_NAME=crm-assets
MINIO_SECURE=false
MINIO_PUBLIC_URL=https://your-domain.com/storage

# ============================================================
# SECURITY CONFIGURATION
# ============================================================

# CRITICAL: Generate a secure secret key (32+ characters)
SECRET_KEY=<GENERATE_SECRET_KEY_HERE>

# IMPORTANT: Set your actual production domain(s)
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# ============================================================
# API PROVIDERS - REQUIRED
# ============================================================

# Lead Discovery (REQUIRED)
APIFY_API_TOKEN=apify_api_XXXXXXXXXXXXXXXXXX
APIFY_MAPS_ACTOR_ID=nwua9Gu5YrADL7ZDj

# AI Services (REQUIRED)
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# AI Fallback (OPTIONAL but recommended)
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXXXXXXXXXXXX

# ============================================================
# API PROVIDERS - OPTIONAL
# ============================================================

# Discovery Fallback Providers
GOOGLE_PLACES_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SEARCH_API_KEY=<YOUR_SERPAPI_KEY>

# Website Enrichment
FIRECRAWL_API_KEY=fc-XXXXXXXXXXXXXXXXXX

# Communication Channels
GMAIL_CLIENT_ID=<YOUR_GMAIL_CLIENT_ID>
GMAIL_CLIENT_SECRET=<YOUR_GMAIL_CLIENT_SECRET>
GMAIL_REFRESH_TOKEN=<YOUR_GMAIL_REFRESH_TOKEN>

WHATSAPP_PHONE_NUMBER_ID=<YOUR_PHONE_NUMBER_ID>
WHATSAPP_ACCESS_TOKEN=<YOUR_WHATSAPP_TOKEN>

# ============================================================
# MONITORING & OBSERVABILITY
# ============================================================

# Error Tracking (HIGHLY RECOMMENDED for production)
SENTRY_DSN=https://xxxxx@o123456.ingest.sentry.io/123456

# ============================================================
# RATE LIMITING
# ============================================================

RATE_LIMIT_DISCOVERY=10/minute
RATE_LIMIT_AI_AGENTS=20/minute
RATE_LIMIT_OUTREACH=10/minute
RATE_LIMIT_DEFAULT=60/minute

# ============================================================
# ADVANCED CONFIGURATION
# ============================================================

# pgvector
PGVECTOR_ENABLED=true
VECTOR_DIMENSION=768

# Job Configuration
MAX_RESULTS_PER_JOB=500
DEFAULT_SEARCH_RADIUS_KM=10
JOB_TIMEOUT_SECONDS=3600

# SSRF Protection
ALLOW_PRIVATE_IPS=false
BLOCKED_DOMAINS=localhost,127.0.0.1,0.0.0.0
```

### 3. Frontend Configuration

Edit `frontend/.env`:

```bash
# Backend API URL
VITE_API_URL=https://your-domain.com/api/v1

# Monitoring (OPTIONAL)
VITE_SENTRY_DSN=https://xxxxx@o123456.ingest.sentry.io/123456

# Environment
VITE_APP_ENV=production
```

### 4. Generate Secure Secrets

**SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**POSTGRES_PASSWORD:**
```bash
openssl rand -base64 24
```

**MINIO_SECRET_KEY:**
```bash
openssl rand -base64 24
```

---

## Database Setup

### 1. Initialize Database

The database will be automatically created on first run via Docker Compose.

### 2. Run Migrations

Migrations run automatically when the backend container starts:

```bash
docker compose up migrate
```

Or manually:
```bash
docker compose exec backend alembic upgrade head
```

### 3. Verify Migrations

Check current migration version:
```bash
docker compose exec backend alembic current
```

Expected output:
```
fbd330059cde (head)
```

### 4. Verify Indexes

Connect to PostgreSQL:
```bash
docker compose exec postgres psql -U postgres -d crm_leads
```

List indexes:
```sql
\di

-- Should show 59 indexes including:
-- idx_business_leads_status
-- idx_business_leads_created_at
-- idx_deals_status
-- idx_contacts_company_id
-- etc.
```

Exit: `\q`

---

## Docker Deployment

### 1. Build Images

```bash
# Navigate to project root
cd /path/to/MVP

# Build all services
docker compose build

# Or build specific service
docker compose build backend
docker compose build frontend
```

### 2. Start Services

**Production deployment:**
```bash
# Start all services in detached mode
docker compose up -d

# View logs
docker compose logs -f
```

**Service startup order:**
1. postgres, redis, minio (infrastructure)
2. migrate (runs database migrations)
3. backend (waits for healthy infrastructure)
4. celery_worker (waits for healthy backend)
5. frontend (waits for healthy backend)

### 3. Verify Services Started

Check service status:
```bash
docker compose ps
```

Expected output:
```
NAME                 STATUS
crm_leads_postgres   Up (healthy)
crm_leads_redis      Up (healthy)
crm_leads_minio      Up (healthy)
crm_leads_backend    Up (healthy)
crm_leads_celery_worker  Up
crm_leads_frontend   Up (healthy)
```

### 4. View Logs

**All services:**
```bash
docker compose logs -f
```

**Specific service:**
```bash
docker compose logs -f backend
docker compose logs -f celery_worker
```

**Last 100 lines:**
```bash
docker compose logs --tail=100 backend
```

---

## Post-Deployment Verification

### 1. Health Check

Test backend health endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "overall": "healthy",
  "postgres": "healthy",
  "redis": "healthy",
  "minio": "healthy",
  "version": "1.0.0"
}
```

### 2. Frontend Accessibility

Test frontend:
```bash
curl -I http://localhost:3000
```

Expected: `200 OK`

Open in browser: `http://localhost:3000`

### 3. API Documentation

Access Swagger docs:
```
http://localhost:8000/docs
```

### 4. Security Headers

Verify security headers:
```bash
curl -I http://localhost:8000/api/v1/health
```

Expected headers:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
X-Request-ID: <uuid>
```

### 5. Rate Limiting

Test rate limit (discovery endpoint, limit: 10/min):
```bash
for i in {1..15}; do 
  curl -X POST http://localhost:8000/api/v1/discovery/jobs \
    -H "Content-Type: application/json" \
    -d '{"query":"test","location":"test"}' \
    -w "\nStatus: %{http_code}\n"
done
```

Expected: First 10 requests succeed, requests 11-15 return `429 Too Many Requests`

### 6. Monitoring Dashboard

Access monitoring dashboard:
```
http://localhost:3000/monitoring
```

Should display real-time status for PostgreSQL, Redis, MinIO.

### 7. Prometheus Metrics

Access metrics endpoint:
```bash
curl http://localhost:8000/metrics
```

Expected: Prometheus-format metrics

---

## Monitoring Setup

### 1. Sentry Error Tracking

If `SENTRY_DSN` is configured:

1. Visit Sentry dashboard: https://sentry.io/
2. Verify events are being received
3. Set up alerts for errors

### 2. Prometheus + Grafana (Optional)

Add to `docker-compose.yml`:

```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"
  networks:
    - crm-lead-network

grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  volumes:
    - grafana_data:/var/lib/grafana
  networks:
    - crm-lead-network
  depends_on:
    - prometheus
```

Create `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'crm-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### 3. Log Aggregation

Configure centralized logging (optional):

**Option A: ELK Stack**
- Elasticsearch for storage
- Logstash for processing
- Kibana for visualization

**Option B: Loki + Grafana**
- Lightweight alternative to ELK
- Integrates with existing Grafana

---

## Troubleshooting

### Issue: Backend Won't Start

**Symptoms:**
- Backend container exits immediately
- Health check fails

**Diagnosis:**
```bash
docker compose logs backend
```

**Common Causes:**

1. **Database not ready:**
   ```
   Solution: Wait for postgres health check to pass
   docker compose ps postgres
   ```

2. **Missing environment variables:**
   ```
   Solution: Check .env file has all required variables
   grep "GEMINI_API_KEY" backend/.env
   ```

3. **Migration failure:**
   ```
   Solution: Check migration logs
   docker compose logs migrate
   ```

4. **Port already in use:**
   ```
   Solution: Check if port 8000 is available
   netstat -ano | findstr :8000
   ```

---

### Issue: Database Connection Errors

**Symptoms:**
- "could not connect to server"
- "FATAL: password authentication failed"

**Diagnosis:**
```bash
docker compose exec backend python -c "from app.core.database import engine; engine.connect()"
```

**Solutions:**

1. **Verify DATABASE_URL:**
   ```bash
   docker compose exec backend env | grep DATABASE_URL
   ```

2. **Check PostgreSQL is healthy:**
   ```bash
   docker compose ps postgres
   # Should show "Up (healthy)"
   ```

3. **Test connection manually:**
   ```bash
   docker compose exec postgres psql -U postgres -d crm_leads -c "SELECT 1"
   ```

---

### Issue: Rate Limiting Not Working

**Symptoms:**
- Can make unlimited requests
- No 429 responses

**Diagnosis:**
```bash
# Check Redis is running
docker compose ps redis

# Check rate limiter configuration
docker compose exec backend python -c "from app.core.rate_limiter import limiter; print(limiter.storage_uri)"
```

**Solutions:**

1. **Verify Redis connection:**
   ```bash
   docker compose exec backend redis-cli -h redis ping
   # Should return "PONG"
   ```

2. **Check middleware is loaded:**
   ```bash
   docker compose logs backend | grep "rate_limit"
   ```

---

### Issue: Frontend Can't Reach Backend

**Symptoms:**
- Network errors in browser console
- API calls fail

**Diagnosis:**
```bash
# Check VITE_API_URL
cat frontend/.env | grep VITE_API_URL

# Test backend from host
curl http://localhost:8000/api/v1/health
```

**Solutions:**

1. **Update VITE_API_URL:**
   ```bash
   # In frontend/.env
   VITE_API_URL=http://localhost:8000/api/v1
   ```

2. **Rebuild frontend:**
   ```bash
   docker compose build frontend
   docker compose up -d frontend
   ```

---

### Issue: High Memory Usage

**Symptoms:**
- Containers being killed (OOM)
- System slowdown

**Diagnosis:**
```bash
docker stats
```

**Solutions:**

1. **Check resource limits:**
   ```bash
   docker inspect crm_leads_backend | grep -A 10 Memory
   ```

2. **Increase container limits (if necessary):**
   ```yaml
   # In docker-compose.yml
   backend:
     deploy:
       resources:
         limits:
           memory: 1G  # Increase from 512M
   ```

3. **Optimize database queries:**
   ```sql
   -- Check slow queries
   SELECT query, calls, total_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC 
   LIMIT 10;
   ```

---

### Issue: Celery Worker Not Processing Jobs

**Symptoms:**
- Jobs stuck in QUEUED status
- Discovery jobs don't complete

**Diagnosis:**
```bash
# Check Celery logs
docker compose logs celery_worker

# Check Redis queue
docker compose exec redis redis-cli LLEN celery
```

**Solutions:**

1. **Restart Celery worker:**
   ```bash
   docker compose restart celery_worker
   ```

2. **Check worker is registered:**
   ```bash
   docker compose exec celery_worker celery -A app.workers.celery_app inspect active
   ```

3. **Verify Celery can reach Redis:**
   ```bash
   docker compose exec celery_worker redis-cli -h redis ping
   ```

---

## Rollback Procedures

### Rollback to Previous Version

**1. Stop current deployment:**
```bash
docker compose down
```

**2. Checkout previous version:**
```bash
git log --oneline -10  # Find commit to rollback to
git checkout <previous-commit>
```

**3. Rollback database (if needed):**
```bash
# Check current migration
docker compose exec backend alembic current

# Downgrade to previous migration
docker compose exec backend alembic downgrade -1
```

**4. Rebuild and restart:**
```bash
docker compose build
docker compose up -d
```

**5. Verify rollback:**
```bash
curl http://localhost:8000/api/v1/health
```

---

### Emergency Shutdown

**Stop all services immediately:**
```bash
docker compose down --remove-orphans
```

**Stop and remove volumes (DESTRUCTIVE - data loss):**
```bash
docker compose down -v
```

---

## Maintenance Operations

### Database Backup

**Manual backup:**
```bash
# Create backup
docker compose exec postgres pg_dump -U postgres crm_leads > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip backup_*.sql
```

**Automated backup script:**
```bash
#!/bin/bash
# save as: backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="crm_leads_${DATE}.sql.gz"

docker compose exec -T postgres pg_dump -U postgres crm_leads | gzip > "${BACKUP_DIR}/${FILENAME}"

# Keep only last 30 days
find ${BACKUP_DIR} -name "crm_leads_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${FILENAME}"
```

**Schedule with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh
```

---

### Database Restore

**From backup file:**
```bash
# Stop backend to prevent writes
docker compose stop backend celery_worker

# Restore
gunzip -c backup_20261110_120000.sql.gz | docker compose exec -T postgres psql -U postgres crm_leads

# Restart services
docker compose start backend celery_worker
```

---

### Update Application

**1. Pull latest code:**
```bash
git fetch origin
git checkout main
git pull origin main
```

**2. Review changes:**
```bash
git log --oneline -10
```

**3. Update environment variables (if needed):**
```bash
# Compare with new .env.example
diff backend/.env backend/.env.example
```

**4. Rebuild containers:**
```bash
docker compose build
```

**5. Run migrations:**
```bash
docker compose run --rm backend alembic upgrade head
```

**6. Restart services:**
```bash
docker compose up -d
```

**7. Verify update:**
```bash
curl http://localhost:8000/api/v1/health
```

---

### Scale Services

**Scale Celery workers:**
```bash
docker compose up -d --scale celery_worker=4
```

**Scale backend (requires load balancer):**
```bash
# Add nginx load balancer first
docker compose up -d --scale backend=3
```

---

### View Resource Usage

**Real-time monitoring:**
```bash
docker stats
```

**Disk usage:**
```bash
docker system df
```

**Clean up unused resources:**
```bash
docker system prune -a
```

---

### Log Rotation

**Configure Docker log rotation:**

Create `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

---

## Production Checklist

### Security

- [ ] HTTPS enabled with valid SSL certificate
- [ ] `SECRET_KEY` is strong and unique (32+ chars)
- [ ] Database password is strong
- [ ] `ALLOWED_ORIGINS` contains only production domains
- [ ] `APP_ENV=production` in backend/.env
- [ ] `DEBUG=false` in backend/.env
- [ ] Firewall configured (only expose 80, 443)
- [ ] Rate limiting enabled
- [ ] Security headers verified

### Monitoring

- [ ] Sentry DSN configured
- [ ] Health checks passing
- [ ] Prometheus metrics accessible
- [ ] Log aggregation configured
- [ ] Alerting rules set up
- [ ] Monitoring dashboard accessible

### Performance

- [ ] Database indexes verified (59 total)
- [ ] Connection pool sized appropriately
- [ ] Resource limits configured
- [ ] Redis caching working
- [ ] Frontend bundle optimized

### Backup & Recovery

- [ ] Automated backups scheduled
- [ ] Backup restoration tested
- [ ] Rollback procedure documented
- [ ] Emergency contacts list created

### Documentation

- [ ] Deployment runbook updated
- [ ] Troubleshooting guide accessible
- [ ] API documentation available
- [ ] Team trained on operations

---

## Support & Contacts

### Emergency Procedures

**System Down:**
1. Check Docker service status
2. Review logs for errors
3. Attempt restart
4. If persistent, execute rollback

**Data Loss:**
1. Stop all write operations
2. Restore from latest backup
3. Verify data integrity
4. Resume operations

**Security Breach:**
1. Immediately revoke compromised credentials
2. Review audit logs
3. Rotate all secrets
4. Notify security team

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying the CRM Lead Discovery platform to production. Follow all steps carefully and verify each checkpoint.

**Key Points:**
- ✅ All environment variables must be configured
- ✅ API keys are required for full functionality
- ✅ Database migrations run automatically
- ✅ Health checks verify successful deployment
- ✅ Monitoring is essential for production operations

For issues not covered in this guide, consult:
- Investigation Report: `.agents/tasks/crm-audit/analysis/investigation-report.md`
- Implementation Review: `.agents/tasks/crm-audit/reviews/implementation-review.md`
- Architecture Diagram: `.agents/tasks/crm-audit/reports/architecture-diagram.md`

---

**Document Version:** 1.0  
**Last Updated:** November 10, 2026  
**Maintained By:** DevOps Team
