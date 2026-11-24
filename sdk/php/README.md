# AI Sales CRM OS — PHP SDK & Webhook Integration Guide

Official PHP SDK and Webhook guide for **AI Sales CRM OS**.  
Is SDK ko specially design kiya gaya hai taaki aap kisi bhi existing PHP CRM (Core PHP, Laravel, CodeIgniter, WordPress, CakePHP ya Custom CRM) mein AI Sales CRM ke powerful features ko **30 seconds** mein integrate kar sakein.

---

## ⚡ Key Highlights (Khaasiyat)

- **Zero External Dependencies**: Na Guzzle chahiye, na koi bhari library. Pure native PHP cURL + JSON use karta hai.
- **Works on All PHP Versions**: Compatible with PHP **7.4, 8.0, 8.1, 8.2, 8.3+**.
- **Drop-in File Support**: Composer nahi use karna? Koi baat nahi! Simply `require_once 'src/AiSalesCrm.php';` karke direct use kar sakte ho.
- **Enterprise HMAC-SHA256 Security**: Webhooks timing-attack safe cryptographic signature ke sath aate hain (`X-CRM-Signature`).
- **Auto Deduplication**: Jab aap CRM se leads push karte ho, system automatically phone, email, website aur company name se duplicate detect karke merge karta hai.

---

## 📁 Folder Structure

```text
sdk/php/
├── composer.json               # Composer package config (optional)
├── README.md                   # Complete Integration documentation
├── src/
│   └── AiSalesCrm.php          # Core SDK Client & Exception classes
└── examples/
    ├── crm_integration.php     # Lead discovery, ingestion, AI qualification script
    └── webhook_receiver.php    # Production-ready webhook listener with HMAC verification
```

---

## 🚀 Quick Start (Kaise Use Karein)

### Option A: Direct File Include (Bina Composer ke — Legacy / Custom PHP)

Bas `sdk/php/src/AiSalesCrm.php` ko apne project mein copy karein aur require karein:

```php
<?php
require_once __DIR__ . '/path/to/AiSalesCrm.php';

use AiSalesCrm\Client;

$crm = new Client('http://localhost:8000', 'optional_api_key');
```

### Option B: Composer Autoloading

Agar aap Laravel, Symfony, ya modern PHP framework use kar rahe hain:

```json
"autoload": {
    "psr-4": {
        "AiSalesCrm\\": "sdk/php/src/"
    }
}
```

```bash
composer dump-autoload
```

---

## 📖 Practical Code Examples

### 1. Ingest Lead (Apne PHP CRM se Lead Push Karein)

Jab aapke CRM mein koi new lead aati hai ya form submit hota hai, use AI Engine mein bhejein:

```php
<?php
require_once 'AiSalesCrm.php';

use AiSalesCrm\Client;

$crm = new Client('http://localhost:8000');

$response = $crm->ingestLead([
    'business_name'   => 'Apollo Dental Clinic',
    'category'        => 'Dentist',
    'email'           => 'care@apollodental.in',
    'phone'           => '+91 99887 76655',
    'website'         => 'https://apollodental.in',
    'city'            => 'Lucknow',
    'state'           => 'Uttar Pradesh',
    'country'         => 'India',
    'source_provider' => 'my_php_crm',
    'external_id'     => '1004', // Aapke local CRM ka ID
]);

$leadId = $response['lead']['id'];
echo "AI Lead Unified ID: " . $leadId;
```

---

### 2. Run Local Google Maps Scraper (Maps se Leads Nikalein)

Directly Python/FastAPI local maps engine ko command dekar leads generate karein:

```php
$discovery = $crm->discoverLeads('Cosmetic Surgeons', 'Lucknow', 10, 'local_maps');

foreach ($discovery['leads'] as $prospect) {
    echo "Business: " . $prospect['business_name'] . " | Phone: " . $prospect['phone'] . "\n";
}
```

---

### 3. Run AI Qualification & cold outreach

Lead ko autonomous AI agent se score karwayen:

```php
// AI ICP Qualification
$qualification = $crm->qualifyLead($leadId);

// Send AI cold email
$crm->sendOutreachEmail(
    $leadId,
    'Quick question regarding your clinic expansion',
    'Hello Doctor, noticed your high ratings in Hazratganj...'
);
```

---

### 4. Setup Webhook (Real-time Events Listen Karein)

Jab AI system kisi lead ko discover kare, qualify kare, ya client cold email ka reply de, to aapke PHP CRM ko turant alert milega.

#### Step 4.1: Register Webhook Subscription
```php
$sub = $crm->createWebhookSubscription(
    'My PHP CRM Webhook',
    'https://your-domain.com/crm/webhook.php',
    ['lead.discovered', 'lead.qualified', 'outreach.replied']
);

$secretKey = $sub['subscription']['secret_key'];
echo "Secret Key: " . $secretKey;
// Ise apne CRM config ya .env file me save karein!
```

#### Step 4.2: Webhook Receiver Script (`webhook.php` on your PHP server)

```php
<?php
require_once 'AiSalesCrm.php';

use AiSalesCrm\Client;

$secretKey = getenv('AI_SALES_CRM_WEBHOOK_SECRET');

// Read raw body & header
$rawPayload = file_get_contents('php://input');
$signature = $_SERVER['HTTP_X_CRM_SIGNATURE'] ?? '';

// Constant-time HMAC-SHA256 signature check
if (!Client::verifyWebhookSignature($rawPayload, $signature, $secretKey)) {
    http_response_code(401);
    echo json_encode(['error' => 'Invalid signature']);
    exit;
}

$event = json_decode($rawPayload, true);
$eventName = $event['event'];
$data = $event['data'];

// Update your local CRM Database
if ($eventName === 'lead.discovered') {
    // Insert into MySQL leads table
} elseif ($eventName === 'lead.qualified') {
    // Update lead score in MySQL
} elseif ($eventName === 'outreach.replied') {
    // Send email/SMS alert to sales rep
}

http_response_code(200);
echo json_encode(['success' => true]);
```

---

## 🔒 Security & Headers

Har webhook request ke sath ye headers deliver hote hain:
- `X-CRM-Signature`: `sha256=<hmac_sha256_hex>`
- `X-CRM-Event`: Event name (jaise `lead.discovered`, `lead.qualified`)
- `X-CRM-Delivery-Id`: Unique UUID for tracking & idempotency
- `X-CRM-Timestamp`: Dispatch timestamp
