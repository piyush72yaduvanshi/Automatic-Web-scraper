<?php
/**
 * Example 1: Full PHP CRM Integration Script
 * 
 * Demonstrates:
 * 1. Initializing client (zero external dependencies)
 * 2. Ingesting existing CRM lead into AI Sales Engine
 * 3. Discovering new local business leads with Google Maps scraper
 * 4. Triggering AI qualification & personalized cold outreach
 * 5. Registering a webhook for real-time notifications
 */

// If using Composer:
// require_once __DIR__ . '/../vendor/autoload.php';

// Or direct include (Works in any legacy/vanilla PHP setup without Composer!):
require_once __DIR__ . '/../src/AiSalesCrm.php';

use AiSalesCrm\Client;
use AiSalesCrm\AiSalesCrmException;

try {
    // 1. Initialize Client
    $crm = new Client('http://localhost:8000', 'optional_api_key_here');
    echo "=== [1/5] AI Sales CRM Client initialized ===\n";

    // 2. Ingest a lead from local PHP CRM database into AI system
    echo "\n=== [2/5] Ingesting CRM Lead to AI Engine ===\n";
    $ingestResult = $crm->ingestLead([
        'business_name'   => 'Dr. Verma Dental Care Clinic',
        'category'        => 'Dentist',
        'email'           => 'contact@vermadental.in',
        'phone'           => '+91 98765 43210',
        'website'         => 'https://vermadental.in',
        'address'         => 'Hazratganj, Near Cathedral School',
        'city'            => 'Lucknow',
        'state'           => 'Uttar Pradesh',
        'country'         => 'India',
        'source_provider' => 'my_php_custom_crm',
        'external_id'     => 'CRM_LEAD_10492', // ID in your local MySQL/PostgreSQL CRM
    ]);

    print_r($ingestResult);
    $leadId = $ingestResult['lead']['id'];
    echo "Lead registered successfully with Unified ID: {$leadId}\n";

    // 3. Trigger AI Qualification
    echo "\n=== [3/5] Running AI Lead Qualification & ICP Scoring ===\n";
    try {
        $qualification = $crm->qualifyLead($leadId);
        echo "AI Qualification Result:\n";
        print_r($qualification);
    } catch (Exception $e) {
        echo "Qualification notice: " . $e->getMessage() . "\n";
    }

    // 4. Discover new high-ticket leads using Local Google Maps Scraper
    echo "\n=== [4/5] Running Google Maps Lead Discovery ===\n";
    $discovery = $crm->discoverLeads('Cosmetic Surgeons', 'Lucknow', 5, 'local_maps');
    echo "Discovered " . count($discovery['leads'] ?? []) . " new prospects via Maps Scraper Engine:\n";
    foreach ($discovery['leads'] ?? [] as $discovered) {
        echo "- " . ($discovered['business_name'] ?? 'Unknown') . " | " . ($discovered['phone'] ?? 'No phone') . " | " . ($discovered['website'] ?? 'No site') . "\n";
    }

    // 5. Register Webhook to listen for replies or automated events
    echo "\n=== [5/5] Registering Webhook Subscription ===\n";
    $webhook = $crm->createWebhookSubscription(
        'Main PHP CRM Production Webhook',
        'https://my-php-crm.example.com/api/webhooks/listener.php',
        ['lead.discovered', 'lead.qualified', 'outreach.replied']
    );

    echo "Webhook Registered Successfully!\n";
    echo "Target URL : " . $webhook['subscription']['target_url'] . "\n";
    echo "Secret Key : " . $webhook['subscription']['secret_key'] . "\n";
    echo "Save this Secret Key in your PHP .env file to verify HMAC signatures!\n";

} catch (AiSalesCrmException $e) {
    echo "SDK Error [Status " . $e->getStatusCode() . "]: " . $e->getMessage() . "\n";
    if ($e->getResponseBody()) {
        print_r($e->getResponseBody());
    }
} catch (Exception $e) {
    echo "Unexpected Error: " . $e->getMessage() . "\n";
}
