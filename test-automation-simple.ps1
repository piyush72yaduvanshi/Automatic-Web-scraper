# Simple Lead Automation Test
# Backend must be running on http://localhost:8000

$baseUrl = "http://localhost:8000/api/v1"
$headers = @{
    'X-API-Key' = 'dev-api-key-12345'
    'Content-Type' = 'application/json'
}

Write-Host "`n=== Testing Lead Automation Implementation ===`n" -ForegroundColor Green

# Test 1: Check automation status
Write-Host "[1] Checking automation status..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/automation/status" -Method Get -Headers $headers
    Write-Host "  SUCCESS - Auto-Enroll: $($response.auto_enroll_enabled), Auto-Approve: $($response.auto_approve_enabled), Auto-CRM: $($response.auto_crm_enabled)" -ForegroundColor Green
    Write-Host "  Min Score Outreach: $($response.min_score_outreach), Min Score CRM: $($response.min_score_crm)" -ForegroundColor White
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: List automation settings
Write-Host "`n[2] Listing automation settings..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/automation/settings" -Method Get -Headers $headers
    Write-Host "  SUCCESS - Found $($response.settings.Count) settings" -ForegroundColor Green
    foreach ($setting in $response.settings) {
        Write-Host "    - $($setting.setting_key): $($setting.setting_value)" -ForegroundColor White
    }
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Check for leads
Write-Host "`n[3] Checking available leads..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/leads?page=1&page_size=10" -Method Get -Headers $headers
    Write-Host "  SUCCESS - Found $($response.total) total leads" -ForegroundColor Green
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Run bulk processing (small batch)
Write-Host "`n[4] Testing bulk processing (5 leads)..." -ForegroundColor Cyan
$body = @{
    batch_size = 5
    min_score = 0
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/leads/bulk-process" -Method Post -Body $body -Headers $headers
    Write-Host "  SUCCESS - Bulk processing completed!" -ForegroundColor Green
    Write-Host "    Processed: $($response.summary.processed)" -ForegroundColor White
    Write-Host "    Succeeded: $($response.summary.succeeded)" -ForegroundColor White
    Write-Host "    Failed: $($response.summary.failed)" -ForegroundColor White
    Write-Host "    Email Enriched: $($response.summary.email_enriched)" -ForegroundColor White
    Write-Host "    Qualified: $($response.summary.qualified)" -ForegroundColor White
    Write-Host "    Enrolled in Outreach: $($response.summary.enrolled)" -ForegroundColor White
    Write-Host "    Converted to CRM: $($response.summary.converted)" -ForegroundColor White
    
    if ($response.summary.errors.Count -gt 0) {
        Write-Host "    Errors:" -ForegroundColor Yellow
        foreach ($error in $response.summary.errors) {
            Write-Host "      - Lead $($error.lead_id): $($error.error)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
}

# Test 5: Check exceptions
Write-Host "`n[5] Checking automation exceptions..." -ForegroundColor Cyan
try {
    $url = "$baseUrl/automation/exceptions?resolved=false&limit=10"
    $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers
    if ($response.total -gt 0) {
        Write-Host "  WARNINGS - Found $($response.total) unresolved exceptions:" -ForegroundColor Yellow
        foreach ($ex in $response.exceptions) {
            Write-Host "    - [$($ex.severity)] $($ex.exception_type): $($ex.reason)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  SUCCESS - No unresolved exceptions" -ForegroundColor Green
    }
} catch {
    Write-Host "  FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Automation Testing Complete ===`n" -ForegroundColor Green
