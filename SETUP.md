# Setup Guide - CRM Lead Discovery Engine

Complete setup instructions for Windows development environment.

## Prerequisites

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **Node.js 18 or higher** - [Download](https://nodejs.org/)
- **PostgreSQL 14 or higher** - [Download](https://www.postgresql.org/download/windows/)
- **Redis** - [Download Windows Version](https://github.com/microsoftarchive/redis/releases)
- **Git** - [Download](https://git-scm.com/download/win)

## Database Setup

### PostgreSQL Installation

1. Download and install PostgreSQL for Windows
2. During installation, set password for `postgres` user
3. Keep default port `5432`

### Create Database

Open PowerShell or Command Prompt:

```powershell
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE crm_leads;

# Exit
\q
```

### Redis Installation

1. Download Redis for Windows from GitHub releases
2. Extract to `C:\Redis`
3. Start Redis:

```powershell
cd C:\Redis
.\redis-server.exe
```

Or install as Windows service:

```powershell
.\redis-server.exe --service-install
.\redis-server.exe --service-start
```

## Backend Setup

### 1. Clone Repository

```powershell
cd d:\
git clone <repository-url> MVP
cd MVP
```

### 2. Create Python Virtual Environment

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```powershell
# Copy example environment file
copy ..\.env.example .env
```

Edit `.env` file and configure:

```env
# Database
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/crm_leads

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys (get from provider websites)
APIFY_API_TOKEN=your_apify_token_here
FIRECRAWL_API_KEY=your_firecrawl_key_here
```

### 5. Run Database Migrations

```powershell
alembic upgrade head
```

### 6. Start Backend Server

```powershell
python main.py
```

Backend will start at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

## Frontend Setup

### 1. Navigate to Frontend Directory

```powershell
cd ..\frontend
```

### 2. Install Dependencies

```powershell
npm install
```

### 3. Configure Environment

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### 4. Start Development Server

```powershell
npm run dev
```

Frontend will start at: **http://localhost:5173**

## Docker Setup (Alternative)

If you prefer Docker:

### 1. Install Docker Desktop for Windows

Download from: https://www.docker.com/products/docker-desktop/

### 2. Start Services

```powershell
docker-compose up -d
```

This starts PostgreSQL and Redis automatically.

## Verify Installation

### 1. Check Backend Health

Open browser: http://localhost:8000/api/v1/health

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "version": "1.0.0"
}
```

### 2. Check Frontend

Open browser: http://localhost:5173

You should see the dashboard.

### 3. Run Tests

```powershell
cd backend
pytest tests/ -v
```

## API Key Setup

See [PROVIDER_SETUP.md](./PROVIDER_SETUP.md) for detailed instructions on getting API keys.

## Troubleshooting

### Port Already in Use

**Backend (port 8000):**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (use PID from above)
taskkill /PID <process_id> /F
```

**Frontend (port 5173):**
```powershell
# Find and kill
netstat -ano | findstr :5173
taskkill /PID <process_id> /F
```

### Database Connection Error

1. Verify PostgreSQL is running:
```powershell
# Check service status
Get-Service postgresql*
```

2. Test connection:
```powershell
psql -U postgres -d crm_leads
```

3. Check DATABASE_URL in `.env`

### Redis Connection Error

1. Verify Redis is running:
```powershell
redis-cli ping
# Should return: PONG
```

2. Check REDIS_URL in `.env`

### Migration Errors

Reset database:

```powershell
# Drop and recreate
psql -U postgres
DROP DATABASE crm_leads;
CREATE DATABASE crm_leads;
\q

# Run migrations again
alembic upgrade head
```

### Python Package Installation Issues

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

## Next Steps

1. Read [PROVIDER_SETUP.md](./PROVIDER_SETUP.md) to configure API providers
2. Read [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for API usage
3. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system design

## Development Workflow

### Daily Workflow

```powershell
# Start PostgreSQL and Redis (if not running as service)
# Terminal 1: Backend
cd d:\MVP\backend
.\venv\Scripts\activate
python main.py

# Terminal 2: Frontend
cd d:\MVP\frontend
npm run dev
```

### Making Database Changes

1. Modify models in `backend/app/models/`
2. Create migration:
```powershell
alembic revision --autogenerate -m "description"
```
3. Review migration in `backend/alembic/versions/`
4. Apply migration:
```powershell
alembic upgrade head
```

### Running Tests

```powershell
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_security.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Support

For issues or questions:
1. Check the logs in backend console
2. Review API documentation at http://localhost:8000/docs
3. Check troubleshooting section above
4. Open an issue on GitHub
