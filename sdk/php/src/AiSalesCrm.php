<?php

namespace AiSalesCrm;

/**
 * Custom Exception for AI Sales CRM SDK errors.
 */
class AiSalesCrmException extends \Exception
{
    protected ?int $statusCode;
    protected ?array $responseBody;

    public function __construct(string $message, int $code = 0, ?int $statusCode = null, ?array $responseBody = null, ?\Throwable $previous = null)
    {
        parent::__construct($message, $code, $previous);
        $this->statusCode = $statusCode;
        $this->responseBody = $responseBody;
    }

    public function getStatusCode(): ?int
    {
        return $this->statusCode;
    }

    public function getResponseBody(): ?array
    {
        return $this->responseBody;
    }
}

/**
 * Enterprise AI Sales CRM PHP Client
 * 
 * Zero external dependencies. Works across Vanilla PHP (7.4 - 8.3+),
 * Laravel, WordPress, CodeIgniter, Symfony, and custom enterprise CRMs.
 */
class Client
{
    protected string $baseUrl;
    protected ?string $apiKey;
    protected int $timeout;
    protected array $defaultHeaders;

    /**
     * @param string $baseUrl Base URL of AI Sales CRM FastAPI backend (e.g. http://localhost:8000 or https://api.crm.com)
     * @param string|null $apiKey Optional Bearer API Token
     * @param int $timeout cURL request timeout in seconds
     */
    public function __construct(string $baseUrl = 'http://localhost:8000', ?string $apiKey = null, int $timeout = 30)
    {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->apiKey = $apiKey;
        $this->timeout = $timeout;
        $this->defaultHeaders = [
            'Accept: application/json',
            'Content-Type: application/json',
            'User-Agent: AiSalesCrm-PHP-SDK/1.0',
        ];

        if ($this->apiKey) {
            $this->defaultHeaders[] = 'Authorization: Bearer ' . $this->apiKey;
        }
    }

    // ==========================================
    // 1. LEAD DISCOVERY & MAPS ENGINE
    // ==========================================

    /**
     * Discover high-value leads using Local Google Maps Scraper or other providers.
     *
     * @param string $query Niche or search keyword (e.g., "Dental Clinic", "B2B SaaS")
     * @param string $location Target city or region (e.g., "Lucknow", "Mumbai", "Dubai")
     * @param int $limit Maximum number of leads to discover
     * @param string $provider 'local_maps' (default: built-in daemon), 'google_places', etc.
     * @return array Discovery result including leads list
     */
    public function discoverLeads(string $query, string $location, int $limit = 10, string $provider = 'local_maps'): array
    {
        return $this->post('/api/v1/discovery/search', [
            'query' => $query,
            'location' => $location,
            'limit' => $limit,
            'provider' => $provider,
        ]);
    }

    /**
     * Get single lead details by ID.
     */
    public function getLead(string $leadId): array
    {
        return $this->get('/api/v1/leads/' . rawurlencode($leadId));
    }

    /**
     * List recent leads with optional filtering and pagination.
     */
    public function listLeads(int $page = 1, int $pageSize = 20, ?string $status = null): array
    {
        $query = [
            'page' => $page,
            'page_size' => $pageSize,
        ];
        if ($status) {
            $query['status'] = $status;
        }
        return $this->get('/api/v1/leads?' . http_build_query($query));
    }

    // ==========================================
    // 2. LEAD INGESTION (PUSH FROM YOUR CRM)
    // ==========================================

    /**
     * Ingest or update a lead pushed directly from your PHP CRM.
     * Deduplicates automatically by website, phone, email, or name+city.
     *
     * @param array $leadData [
     *     'business_name'   => (required) string,
     *     'category'        => (optional) string,
     *     'email'           => (optional) string,
     *     'phone'           => (optional) string,
     *     'website'         => (optional) string,
     *     'address'         => (optional) string,
     *     'city'            => (optional) string,
     *     'state'           => (optional) string,
     *     'country'         => (optional) string,
     *     'source_provider' => (optional) string,
     *     'external_id'     => (optional) string (ID from your local PHP CRM),
     * ]
     * @return array Ingestion confirmation with unified lead ID
     */
    public function ingestLead(array $leadData): array
    {
        return $this->post('/api/v1/webhooks/ingest', $leadData);
    }

    // ==========================================
    // 3. AI QUALIFICATION & ENRICHMENT
    // ==========================================

    /**
     * Trigger autonomous AI evaluation and scoring for a lead.
     */
    public function qualifyLead(string $leadId): array
    {
        return $this->post("/api/v1/leads/{$leadId}/qualify", []);
    }

    /**
     * Enrich lead with deep email and contact discovery.
     */
    public function enrichLead(string $leadId): array
    {
        return $this->post("/api/v1/leads/{$leadId}/enrich", []);
    }

    // ==========================================
    // 4. MULTI-CHANNEL OUTREACH
    // ==========================================

    /**
     * Dispatch an AI-personalized outreach email.
     */
    public function sendOutreachEmail(string $leadId, string $subject, ?string $body = null): array
    {
        return $this->post('/api/v1/outreach/send', [
            'lead_id' => $leadId,
            'channel' => 'EMAIL',
            'subject' => $subject,
            'body' => $body,
        ]);
    }

    // ==========================================
    // 5. WEBHOOK MANAGEMENT
    // ==========================================

    /**
     * Register a new webhook endpoint to receive real-time events in your PHP CRM.
     *
     * @param string $name Descriptive name (e.g. "Main Laravel CRM Hook")
     * @param string $targetUrl Publicly accessible HTTPS URL in your PHP CRM
     * @param array $events Event types to subscribe to (e.g. ['lead.discovered', 'lead.qualified', 'outreach.replied'] or ['*'])
     * @param array $headers Optional custom HTTP headers sent with every dispatch
     * @return array Webhook subscription details including generated `secret_key`
     */
    public function createWebhookSubscription(string $name, string $targetUrl, array $events = ['*'], array $headers = []): array
    {
        return $this->post('/api/v1/webhooks/subscriptions', [
            'name' => $name,
            'target_url' => $targetUrl,
            'events' => $events,
            'custom_headers' => $headers,
        ]);
    }

    /**
     * List all active webhook subscriptions.
     */
    public function listWebhookSubscriptions(): array
    {
        return $this->get('/api/v1/webhooks/subscriptions');
    }

    /**
     * Delete a webhook subscription by ID.
     */
    public function deleteWebhookSubscription(string $subscriptionId): bool
    {
        $this->delete('/api/v1/webhooks/subscriptions/' . rawurlencode($subscriptionId));
        return true;
    }

    /**
     * Send a ping/test payload to verify your PHP CRM receiver endpoint.
     */
    public function testWebhookSubscription(string $subscriptionId): array
    {
        return $this->post("/api/v1/webhooks/subscriptions/{$subscriptionId}/test", []);
    }

    // ==========================================
    // 6. CRYPTOGRAPHIC SIGNATURE VERIFICATION
    // ==========================================

    /**
     * Verify incoming webhook authenticity using HMAC-SHA256 constant-time comparison.
     * Crucial to prevent replay and forgery attacks on your PHP CRM.
     *
     * @param string $rawPayload Exactly file_get_contents('php://input')
     * @param string $signatureHeader Header value from $_SERVER['HTTP_X_CRM_SIGNATURE']
     * @param string $secretKey Secret key received during webhook creation
     * @return bool True if valid, False if forged or tampered
     */
    public static function verifyWebhookSignature(string $rawPayload, string $signatureHeader, string $secretKey): bool
    {
        if (empty($signatureHeader) || empty($secretKey)) {
            return false;
        }

        $cleanHeader = str_replace('sha256=', '', trim($signatureHeader));
        $expected = hash_hmac('sha256', $rawPayload, $secretKey);

        return hash_equals($expected, $cleanHeader);
    }

    // ==========================================
    // INTERNAL HTTP ENGINE (cURL)
    // ==========================================

    protected function get(string $path): array
    {
        return $this->request('GET', $path);
    }

    protected function post(string $path, array $data = []): array
    {
        return $this->request('POST', $path, $data);
    }

    protected function delete(string $path): array
    {
        return $this->request('DELETE', $path);
    }

    protected function request(string $method, string $path, ?array $data = null): array
    {
        $url = $this->baseUrl . '/' . ltrim($path, '/');
        $ch = curl_init();

        $headers = $this->defaultHeaders;

        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);

        if ($data !== null && in_array($method, ['POST', 'PUT', 'PATCH'])) {
            $payload = json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
            $headers[] = 'Content-Length: ' . strlen($payload);
        }

        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlError = curl_error($ch);
        $curlErrno = curl_errno($ch);
        curl_close($ch);

        if ($curlErrno !== 0) {
            throw new AiSalesCrmException("cURL Network Error [{$curlErrno}]: {$curlError}", $curlErrno);
        }

        $decoded = json_decode($response, true);

        if ($httpCode >= 400) {
            $msg = "AI Sales CRM API Error [HTTP {$httpCode}]";
            if (is_array($decoded) && isset($decoded['detail'])) {
                $msg .= ": " . (is_array($decoded['detail']) ? json_encode($decoded['detail']) : $decoded['detail']);
            } elseif (is_string($response) && strlen($response) > 0) {
                $msg .= ": " . substr($response, 0, 200);
            }
            throw new AiSalesCrmException($msg, $httpCode, $httpCode, is_array($decoded) ? $decoded : null);
        }

        return is_array($decoded) ? $decoded : ['raw_response' => $response];
    }
}
