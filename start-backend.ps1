# Start Backend Server
# Requires: PostgreSQL running, Python 3.11+, virtual environment activated

Write-Host "🚀 Starting AI Sales & CRM Backend Server..." -ForegroundColor Green
Write-Host ""

# Check if in MVP directory
if (-not (Test-Path ".\backend")) {
    Write-Host "❌ Error: Must run from MVP root directory" -ForegroundColor Red
    exit 1
}

# Navigate to backend
Set-Location backend

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ Error: .env file not found in backend/" -ForegroundColor Red
    Write-Host "   Copy .env.example to .env and configure DATABASE_URL" -ForegroundColor Yellow
    exit 1
}

# Check if database is reachable (optional)
Write-Host "🔍 Checking database connection..." -ForegroundColor Cyan
python -c "from app.core.database import engine; print('✅ Database connected')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Could not connect to database" -ForegroundColor Yellow
    Write-Host "   Make sure PostgreSQL is running" -ForegroundColor Yellow
    Write-Host ""
}

# Run migrations
Write-Host "📦 Running database migrations..." -ForegroundColor Cyan
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Migration failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Migrations complete" -ForegroundColor Green
Write-Host ""

# Start server
Write-Host "🌐 Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔧 Admin Panel: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
