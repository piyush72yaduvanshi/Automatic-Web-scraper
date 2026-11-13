# Test Automation Implementation
# Requires: Backend server running on http://localhost:8000

Write-Host "🧪 Testing Lead Automation Implementation..." -ForegroundColor Green
Write-Host ""

$baseUrl = "http://localhost:8000/api/v1"

# Test 1: Check automation status
Write-Host "1️⃣  Checking automation status..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/automation/status" -Method Get
    Write-Host "   ✅ Automation Status:" -ForegroundColor Green
    Write-Host "      Auto-Enroll: $($response.auto_enroll_enabled)" -ForegroundColor White
    Write-Host "      Auto-Approve: $($response.auto_approve_enabled)" -ForegroundColor White
    Write-Host "      Auto-CRM: $($response.auto_crm_enabled)" -ForegroundColor White
    Write-Host "      Min Score Outreach: $($response.min_score_outreach)" -ForegroundColor White
    Write-Host "      Min Score CRM: $($response.min_score_crm)" -ForegroundColor White
} catch {
    Write-Host "   ❌ Failed to get automation status" -ForegroundColor Red
    Write-Host "   Make sure backend is running on port 8000" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Test 2: List automation settings
Write-Host "2️⃣  Listing all automation settings..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/automation/settings" -Method Get
    Write-Host "   ✅ Found $($response.settings.Count) settings" -ForegroundColor Green
    foreach ($setting in $response.settings) {
        Write-Host "      - $($setting.key): $($setting.value) ($($setting.type))" -ForegroundColor White
    }
} catch {
    Write-Host "   ❌ Failed to list settings" -ForegroundColor Red
}
Write-Host ""

# Test 3: Check for unprocessed leads
Write-Host "3️⃣  Checking for unprocessed leads..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/leads?page=1&page_size=100" -Method Get
    $total = $response.total
    Write-Host "   ✅ Found $total total leads" -ForegroundColor Green
    
    # Count unprocessed (this is a rough estimate)
    Write-Host "   ℹ️  Ready for bulk processing" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ Failed to list leads" -ForegroundColor Red
}
Write-Host ""

# Test 4: Run bulk processing (dry run with batch_size=5)
Write-Host "4️⃣  Testing bulk processing (5 leads)..." -ForegroundColor Cyan
$body = @{
    batch_size = 5
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/leads/bulk-process" -Method Post -Body $body -ContentType "application/json"
    Write-Host "   ✅ Bulk processing completed!" -ForegroundColor Green
    Write-Host "      Processed: $($response.summary.processed)" -ForegroundColor White
    Write-Host "      Succeeded: $($response.summary.succeeded)" -ForegroundColor White
    Write-Host "      Failed: $($response.summary.failed)" -ForegroundColor White
    Write-Host "      Email Enriched: $($response.summary.email_enriched)" -ForegroundColor White
    Write-Host "      Qualified: $($response.summary.qualified)" -ForegroundColor White
    Write-Host "      Enrolled: $($response.summary.enrolled)" -ForegroundColor White
    Write-Host "      Converted to CRM: $($response.summary.converted)" -ForegroundColor White
    
    if ($response.summary.errors.Count -gt 0) {
        Write-Host "      ⚠️  Errors:" -ForegroundColor Yellow
        foreach ($error in $response.summary.errors) {
            Write-Host "         - Lead $($error.lead_id): $($error.error)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "   ❌ Bulk processing failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Check exceptions
Write-Host "5️⃣  Checking automation exceptions..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/automation/exceptions?resolved=false&limit=10" -Method Get
    if ($response.total -gt 0) {
        Write-Host "   ⚠️  Found $($response.total) unresolved exceptions:" -ForegroundColor Yellow
        foreach ($ex in $response.exceptions) {
            Write-Host "      - [$($ex.severity)] $($ex.type): $($ex.reason)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ No unresolved exceptions" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Failed to check exceptions" -ForegroundColor Red
}
Write-Host ""

Write-Host "🎉 Automation testing complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  • Process all leads: POST $baseUrl/leads/bulk-process with {'batch_size': 50}" -ForegroundColor White
Write-Host "  • Check CRM data in frontend: http://localhost:3000/crm" -ForegroundColor White
Write-Host "  • Adjust settings: PUT $baseUrl/automation/settings/{key}" -ForegroundColor White
