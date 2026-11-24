<?php
/**
 * Example 2: Enterprise Webhook Receiver Endpoint for PHP
 * 
 * Place this file as `webhook_receiver.php` in your PHP webroot or route.
 * 
 * Features:
 * - Constant-time HMAC-SHA256 signature verification (Timing attack resistant)
 * - Safe JSON event extraction
 * - Updates local CRM database (MySQL / PDO) based on event type
 * - Returns 200 OK fast to acknowledge receipt
 */

// If using Composer:
// require_once __DIR__ . '/../vendor/autoload.php';

// Direct include:
require_once __DIR__ . '/../src/AiSalesCrm.php';

use AiSalesCrm\Client;

// 1. Webhook Secret Key (Stored in your CRM config or .env)
$webhookSecret = getenv('AI_SALES_CRM_WEBHOOK_SECRET') ?: 'your_saved_webhook_secret_key_here';

// 2. Read raw incoming payload and signature header
$rawPayload = file_get_contents('php://input');
$signatureHeader = $_SERVER['HTTP_X_CRM_SIGNATURE'] ?? '';
$deliveryId = $_SERVER['HTTP_X_CRM_DELIVERY_ID'] ?? '';
$eventType = $_SERVER['HTTP_X_CRM_EVENT'] ?? '';

// 3. Cryptographic Verification (HMAC-SHA256)
$isValid = Client::verifyWebhookSignature($rawPayload, $signatureHeader, $webhookSecret);

if (!$isValid) {
    http_response_code(401);
    header('Content-Type: application/json');
    echo json_encode([
        'success' => false,
        'error' => 'Invalid or forged HMAC signature. Webhook rejected.',
    ]);
    exit;
}

// 4. Decode JSON Event Body
$event = json_decode($rawPayload, true);
if (!$event) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Malformed JSON']);
    exit;
}

$eventName = $event['event'] ?? $eventType;
$data = $event['data'] ?? [];

// 5. Route event to your local CRM Business Logic
switch ($eventName) {
    case 'lead.discovered':
        // A new lead was scraped from Google Maps or Multi-Source
        // TODO: Insert lead into your local PHP CRM table (e.g., `crm_leads`)
        // Example PDO:
        // $stmt = $pdo->prepare("INSERT INTO crm_leads (name, phone, email, website) VALUES (?, ?, ?, ?)");
        // $stmt->execute([$data['business_name'], $data['phone'], $data['email'], $data['website']]);
        error_log("[CRM Webhook] Discovered lead: " . ($data['business_name'] ?? 'N/A'));
        break;

    case 'lead.qualified':
        // AI completed ICP evaluation and assigned a score
        $leadId = $data['lead_id'] ?? null;
        $score = $data['qualification_score'] ?? 0;
        $status = $data['qualification_status'] ?? 'Unknown';
        // TODO: Update lead score in your PHP CRM
        // $pdo->prepare("UPDATE crm_leads SET ai_score = ?, ai_status = ? WHERE ai_lead_id = ?")->execute([$score, $status, $leadId]);
        error_log("[CRM Webhook] Lead qualified: {$leadId} - Score: {$score}");
        break;

    case 'outreach.replied':
        // Prospect replied to cold email or LinkedIn message!
        // TODO: Send instant Slack/WhatsApp alert or notify sales agent in PHP CRM
        error_log("[CRM Webhook] Prospect Replied! Lead: " . ($data['lead_id'] ?? 'N/A'));
        break;

    case 'system.test':
        error_log("[CRM Webhook] Test ping received from AI Sales CRM");
        break;

    default:
        error_log("[CRM Webhook] Unhandled event: " . $eventName);
        break;
}

// 6. Return 200 OK immediately
http_response_code(200);
header('Content-Type: application/json');
echo json_encode([
    'success' => true,
    'message' => 'Event received and processed successfully',
    'delivery_id' => $deliveryId,
]);
exit;
