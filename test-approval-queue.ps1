# Test Approval Queue - Quick Script
# Creates test lead and generates draft email

Write-Host "`n🧪 APPROVAL QUEUE TEST SCRIPT" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

$headers = @{
    "X-API-Key" = "test-api-key-2025"
    "Content-Type" = "application/json"
}

$baseUrl = "http://localhost:8000/api/v1"

Write-Host "`nStep 1: Creating test lead..." -ForegroundColor Yellow

$leadBody = @{
    company_name = "Test Restaurant Mumbai"
    email = "test@example.com"  # CHANGE THIS TO YOUR EMAIL
    phone = "+91-9876543210"
    industry = "Restaurant"
    city = "Mumbai"
    status = "qualified"
    source = "manual_test"
    metadata = @{
        test = $true
        created_by = "test_script"
    }
} | ConvertTo-Json

try {
    $lead = Invoke-RestMethod -Uri "$baseUrl/leads" `
        -Method POST -Headers $headers -Body $leadBody -ErrorAction Stop
    
    Write-Host "✓ Lead created successfully!" -ForegroundColor Green
    Write-Host "  Lead ID: $($lead.id)" -ForegroundColor Gray
    Write-Host "  Company: $($lead.company_name)" -ForegroundColor Gray
    Write-Host "  Email: $($lead.email)" -ForegroundColor Gray
    
    $leadId = $lead.id
    
} catch {
    Write-Host "✗ Failed to create lead" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "`nTroubleshooting:" -ForegroundColor Cyan
    Write-Host "  1. Is backend running? Check: http://localhost:8000/api/v1/health" -ForegroundColor Gray
    Write-Host "  2. Is API key correct?" -ForegroundColor Gray
    Write-Host "  3. Check backend logs for errors" -ForegroundColor Gray
    exit 1
}

Write-Host "`nStep 2: Generating outreach draft..." -ForegroundColor Yellow

$draftBody = @{
    lead_id = $leadId
    template_type = "cold_intro"
    sequence_name = "B2B_PROSPECTING"
    personalization = @{
        company_name = "Test Restaurant Mumbai"
        industry = "Restaurant"
        city = "Mumbai"
        first_name = "Owner"
    }
} | ConvertTo-Json

try {
    $draft = Invoke-RestMethod -Uri "$baseUrl/outreach/drafts" `
        -Method POST -Headers $headers -Body $draftBody -ErrorAction Stop
    
    Write-Host "✓ Draft created successfully!" -ForegroundColor Green
    Write-Host "  Draft ID: $($draft.id)" -ForegroundColor Gray
    Write-Host "  Subject: $($draft.subject)" -ForegroundColor Gray
    Write-Host "  Status: $($draft.status)" -ForegroundColor Gray
    
} catch {
    Write-Host "⚠ Draft creation endpoint might not exist yet" -ForegroundColor Yellow
    Write-Host "  This is OK - using alternative method..." -ForegroundColor Gray
    
    # Alternative: Enroll in sequence
    Write-Host "`n  Trying sequence enrollment instead..." -ForegroundColor Yellow
    
    $enrollBody = @{
        lead_ids = @($leadId)
        sequence_name = "B2B_PROSPECTING"
    } | ConvertTo-Json
    
    try {
        Invoke-RestMethod -Uri "$baseUrl/sequences/enroll" `
            -Method POST -Headers $headers -Body $enrollBody -ErrorAction Stop
        
        Write-Host "  ✓ Lead enrolled in sequence!" -ForegroundColor Green
        Write-Host "  This will generate 4 drafts in approval queue" -ForegroundColor Gray
        
    } catch {
        Write-Host "  ✗ Sequence enrollment also failed" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host "`nStep 3: Checking approval queue..." -ForegroundColor Yellow

try {
    $queue = Invoke-RestMethod -Uri "$baseUrl/outreach/queue?status=PENDING" `
        -Headers $headers -ErrorAction Stop
    
    if ($queue.Count -gt 0) {
        Write-Host "✓ Found $($queue.Count) draft(s) in queue!" -ForegroundColor Green
        Write-Host ""
        $queue | ForEach-Object {
            Write-Host "  📧 Draft:" -ForegroundColor Cyan
            Write-Host "    To: $($_.recipient_email)" -ForegroundColor Gray
            Write-Host "    Subject: $($_.subject)" -ForegroundColor Gray
            Write-Host "    Status: $($_.status)" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "⚠ Queue is still empty" -ForegroundColor Yellow
        Write-Host "  Drafts might take a few seconds to appear..." -ForegroundColor Gray
    }
    
} catch {
    Write-Host "⚠ Could not check queue" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host "`n✅ TEST COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open: http://localhost:5173/outreach" -ForegroundColor White
Write-Host "  2. Go to: Approval Queue tab" -ForegroundColor White
Write-Host "  3. Status: PENDING" -ForegroundColor White
Write-Host "  4. Review and approve drafts" -ForegroundColor White
Write-Host ""
Write-Host "If queue is empty:" -ForegroundColor Cyan
Write-Host "  • Wait 10-20 seconds and refresh" -ForegroundColor Gray
Write-Host "  • Check backend logs (Terminal 12)" -ForegroundColor Gray
Write-Host "  • Try manual 'Draft Outreach' in UI" -ForegroundColor Gray
Write-Host ""

# Database verification
Write-Host "Database Verification:" -ForegroundColor Yellow
Write-Host "  Checking outreach_queue table..." -ForegroundColor Gray

try {
    $dbCheck = docker exec crm_leads_postgres psql -U postgres -d crm_leads -t -c "SELECT COUNT(*) FROM outreach_queue WHERE status = 'PENDING_APPROVAL';" 2>$null
    $count = $dbCheck.Trim()
    
    Write-Host "  ✓ Pending drafts in database: $count" -ForegroundColor Green
    
    if ($count -gt 0) {
        Write-Host "`n  📊 Latest draft details:" -ForegroundColor Cyan
        docker exec crm_leads_postgres psql -U postgres -d crm_leads -c "SELECT recipient_email, subject, status, created_at FROM outreach_queue WHERE status = 'PENDING_APPROVAL' ORDER BY created_at DESC LIMIT 3;" 2>$null
    }
    
} catch {
    Write-Host "  ⚠ Could not verify database (Docker might be offline)" -ForegroundColor Yellow
}

Write-Host ""
