# Start Frontend Development Server
# Requires: Node.js 18+, npm packages installed

Write-Host "🚀 Starting AI Sales & CRM Frontend..." -ForegroundColor Green
Write-Host ""

# Check if in MVP directory
if (-not (Test-Path ".\frontend")) {
    Write-Host "❌ Error: Must run from MVP root directory" -ForegroundColor Red
    exit 1
}

# Navigate to frontend
Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm install failed" -ForegroundColor Red
        exit 1
    }
}

# Start dev server
Write-Host "🌐 Starting React development server..." -ForegroundColor Green
Write-Host "📱 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔗 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm run dev
