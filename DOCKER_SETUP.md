# Docker Setup Guide - CRM Lead Discovery Engine

Complete Docker setup for running the entire application in containers.

## Prerequisites

### Required Software

1. **Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop/
   - Minimum version: 20.10+
   - Enable WSL 2 backend (recommended)

2. **PowerShell** (comes with Windows)

### System Requirements

- Windows 10/11 Pro, Enterprise, or Education (for Hyper-V)
- OR Windows 10/11 Home with WSL 2
- 8 GB RAM minimum (16 GB recommended)
- 20 GB free disk space

## Quick Start

### 1. Install Docker Desktop

1. Download and install Docker Desktop
2. Start Docker Desktop
3. Wait for "Docker Desktop is running" status
4. Verify installation:

```powershell
docker --version
docker compose version
```

Expected output:
```
Docker version 24.0.x
Docker Compose version v2.x.x
```

### 2. Configure Environment

```powershell
# Navigate to project
cd d:\MVP

# Create .env file from example
copy .env.example .env

# Edit .env with your credentials (optional for MVP)
notepad .env
```

**Minimum Configuration:**

```env
# Database (already configured for Docker)
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/crm_leads

# Redis (already configured for Docker)
REDIS_URL=redis://redis:6379/0

# Optional: Add API keys for real data
APIFY_API_TOKEN=your_token_here
FIRECRAWL_API_KEY=your_key_here
```

### 3. Build and Start

```powershell
# Build all images
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps
```

### 4. Run Migrations

```powershell
# Run database migrations
docker compose run --rm migrate

# OR if already started, exec into backend
docker compose exec backend alembic upgrade head
```

### 5. Access Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

## Docker Services

### Service Architecture

```
┌─────────────┐
│  Frontend   │ :3000 (nginx)
│   (React)   │
└──────┬──────┘
       │
       ▼ /api/* proxy
┌─────────────┐
│   Backend   │ :8000 (FastAPI)
│   (Python)  │
└──────┬──────┘
       │
       ├──► PostgreSQL :5432
       ├──► Redis :6379
       │
┌──────┴──────┐
│   Celery    │
│   Worker    │
└─────────────┘
```

### Service Details

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| frontend | crm_leads_frontend | 3000 | React + nginx |
| backend | crm_leads_backend | 8000 | FastAPI API |
| celery_worker | crm_leads_celery_worker | - | Background jobs |
| postgres | crm_leads_postgres | 5432 | Database |
| redis | crm_leads_redis | 6379 | Cache/Queue |

## Common Commands

### Starting and Stopping

```powershell
# Start all services
docker compose up -d

# Start specific service
docker compose up -d backend

# Stop all services
docker compose stop

# Stop and remove containers (preserves data)
docker compose down

# Stop and remove containers with volumes (deletes data)
docker compose down -v
```

### Viewing Logs

```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Service Status

```powershell
# Check running services
docker compose ps

# Check service health
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"

# Detailed inspect
docker inspect crm_leads_backend
```

### Database Operations

```powershell
# Connect to PostgreSQL
docker compose exec postgres psql -U postgres -d crm_leads

# Run SQL file
docker compose exec -T postgres psql -U postgres -d crm_leads < backup.sql

# Create backup
docker compose exec postgres pg_dump -U postgres crm_leads > backup.sql

# Check database size
docker compose exec postgres psql -U postgres -c "\l+ crm_leads"
```

### Redis Operations

```powershell
# Connect to Redis CLI
docker compose exec redis redis-cli

# Check Redis info
docker compose exec redis redis-cli INFO

# Monitor Redis commands
docker compose exec redis redis-cli MONITOR
```

### Running Tests

```powershell
# Backend tests
docker compose exec backend pytest -v

# Specific test file
docker compose exec backend pytest tests/test_security.py -v

# With coverage
docker compose exec backend pytest --cov=app --cov-report=html
```

### Rebuilding

```powershell
# Rebuild all images
docker compose build

# Rebuild specific service
docker compose build backend

# Rebuild without cache
docker compose build --no-cache

# Rebuild and restart
docker compose up -d --build
```

### Database Migrations

```powershell
# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Check current version
docker compose exec backend alembic current

# Migration history
docker compose exec backend alembic history
```

## Environment Variables

### Backend Service

All backend environment variables are configured in `docker-compose.yml`.

**Key Variables:**

- `DATABASE_URL` - PostgreSQL connection (uses service name `postgres`)
- `REDIS_URL` - Redis connection (uses service name `redis`)
- `APIFY_API_TOKEN` - Apify API key (from .env)
- `FIRECRAWL_API_KEY` - Firecrawl API key (from .env)

### Docker Service Names

**IMPORTANT:** Inside containers, use Docker service names for networking:

- Database host: `postgres` (NOT `localhost`)
- Redis host: `redis` (NOT `localhost`)
- Backend host: `backend` (for inter-container communication)

## Troubleshooting

### Service Won't Start

```powershell
# Check logs
docker compose logs backend

# Check health
docker compose ps

# Restart service
docker compose restart backend
```

### Port Already in Use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <process_id> /F

# Change port in docker-compose.yml
# ports:
#   - "8001:8000"  # Use 8001 instead
```

### Database Connection Failed

```powershell
# Check PostgreSQL is running
docker compose ps postgres

# Check health
docker compose exec postgres pg_isready -U postgres

# Restart PostgreSQL
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### Redis Connection Failed

```powershell
# Check Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping

# Restart Redis
docker compose restart redis
```

### Frontend Can't Reach Backend

**Check:**

1. Backend is running: `docker compose ps backend`
2. Backend health: `curl http://localhost:8000/api/v1/health`
3. Nginx config is correct
4. Check browser console for errors

### Celery Worker Not Processing Jobs

```powershell
# Check worker logs
docker compose logs -f celery_worker

# Check Redis connection
docker compose exec celery_worker redis-cli -h redis ping

# Restart worker
docker compose restart celery_worker

# Check Celery tasks
docker compose exec backend python -c "from app.workers.celery_app import celery_app; print(celery_app.tasks)"
```

### Out of Disk Space

```powershell
# Check Docker disk usage
docker system df

# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes (CAREFUL: deletes data)
docker volume prune

# Clean everything (CAREFUL)
docker system prune -a --volumes
```

### Build Failures

```powershell
# Clear build cache
docker builder prune

# Rebuild without cache
docker compose build --no-cache

# Check Dockerfile syntax
docker compose config
```

## Development Workflow

### Local Development with Docker

```powershell
# Start services
docker compose up -d

# Watch backend logs
docker compose logs -f backend

# Make code changes (auto-reload if volume mounted)

# Run tests
docker compose exec backend pytest

# Restart if needed
docker compose restart backend
```

### Adding New Dependencies

**Backend:**

1. Add to `backend/requirements.txt`
2. Rebuild: `docker compose build backend`
3. Restart: `docker compose up -d backend`

**Frontend:**

1. Add to `frontend/package.json`
2. Rebuild: `docker compose build frontend`
3. Restart: `docker compose up -d frontend`

## Data Persistence

### Volumes

Docker volumes persist data across container restarts:

- `crm_leads_postgres_data` - PostgreSQL data
- `crm_leads_redis_data` - Redis data

### Backup Data

```powershell
# Backup database
docker compose exec postgres pg_dump -U postgres crm_leads > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Backup Redis
docker compose exec redis redis-cli SAVE
docker cp crm_leads_redis:/data/dump.rdb ./redis_backup_$(Get-Date -Format "yyyyMMdd_HHmmss").rdb
```

### Restore Data

```powershell
# Restore database
Get-Content backup.sql | docker compose exec -T postgres psql -U postgres crm_leads

# Restore Redis
docker cp redis_backup.rdb crm_leads_redis:/data/dump.rdb
docker compose restart redis
```

## Production Considerations

### Security

1. **Change default passwords:**
```yaml
environment:
  POSTGRES_PASSWORD: strong_secure_password
```

2. **Remove port exposures:**
```yaml
# Remove these lines in production:
ports:
  - "5432:5432"  # Don't expose PostgreSQL
  - "6379:6379"  # Don't expose Redis
```

3. **Use Docker secrets:**
```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

4. **Set SECRET_KEY:**
```env
SECRET_KEY=random-secure-key-minimum-32-characters
```

### Scaling

```powershell
# Scale Celery workers
docker compose up -d --scale celery_worker=3

# Check scaled services
docker compose ps
```

### Health Monitoring

```powershell
# Check all health statuses
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.Health}}"

# Automated health check script
while ($true) {
    docker compose ps --format "table {{.Service}}\t{{.Health}}"
    Start-Sleep -Seconds 30
}
```

## Testing Checklist

Run these tests after setup:

- [ ] All containers start: `docker compose ps`
- [ ] All health checks pass
- [ ] Backend API responds: `curl http://localhost:8000/api/v1/health`
- [ ] Frontend loads: Open http://localhost:3000
- [ ] Database migrations complete
- [ ] Celery worker connects to Redis
- [ ] Create test discovery job
- [ ] Job executes successfully
- [ ] Leads saved to database
- [ ] CSV export works
- [ ] Automated tests pass: `docker compose exec backend pytest`

## Support

### Logs Location

```powershell
# Container logs
docker compose logs

# Docker daemon logs (Windows)
Get-EventLog -LogName Application -Source Docker -Newest 50
```

### Getting Help

1. Check logs: `docker compose logs -f`
2. Check health: `docker compose ps`
3. Verify configuration: `docker compose config`
4. Review this guide
5. Check main SETUP.md
6. Open issue with logs

## Quick Reference

```powershell
# Start everything
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f backend

# Run tests
docker compose exec backend pytest -v

# Access database
docker compose exec postgres psql -U postgres -d crm_leads

# Access Redis
docker compose exec redis redis-cli

# Stop everything
docker compose down

# Stop and delete data
docker compose down -v

# Rebuild and start
docker compose up -d --build
```
