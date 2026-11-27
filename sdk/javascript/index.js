const crypto = require('crypto');

class AiSalesCrmError extends Error {
  constructor(message, statusCode = null, responseBody = null) {
    super(message);
    this.name = 'AiSalesCrmError';
    this.statusCode = statusCode;
    this.responseBody = responseBody;
  }
}

class AiSalesCrm {
  constructor({ baseUrl = 'http://localhost:8000', apiKey = null, timeout = 30000 } = {}) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.apiKey = apiKey;
    this.timeout = timeout;
  }

  // 1. Lead Discovery & Maps Engine
  async discoverLeads({ query, location, limit = 10, provider = 'local_maps' }) {
    return this.post('/api/v1/discovery/search', { query, location, limit, provider });
  }

  async getLead(leadId) {
    return this.get(`/api/v1/leads/${encodeURIComponent(leadId)}`);
  }

  async listLeads({ page = 1, pageSize = 20, status = null } = {}) {
    const params = new URLSearchParams({ page, page_size: pageSize });
    if (status) params.set('status', status);
    return this.get(`/api/v1/leads?${params.toString()}`);
  }

  // 2. Ingest Lead from External CRM
  async ingestLead(leadData) {
    return this.post('/api/v1/webhooks/ingest', leadData);
  }

  // 3. AI Qualification & Enrichment
  async qualifyLead(leadId) {
    return this.post(`/api/v1/leads/${encodeURIComponent(leadId)}/qualify`, {});
  }

  async enrichLead(leadId) {
    return this.post(`/api/v1/leads/${encodeURIComponent(leadId)}/enrich`, {});
  }

  // 4. Multi-Channel Outreach
  async sendOutreachEmail({ leadId, subject, body = null }) {
    return this.post('/api/v1/outreach/send', {
      lead_id: leadId,
      channel: 'EMAIL',
      subject,
      body,
    });
  }

  // 5. Webhook Management
  async createWebhookSubscription({ name, targetUrl, events = ['*'], customHeaders = {} }) {
    return this.post('/api/v1/webhooks/subscriptions', {
      name,
      target_url: targetUrl,
      events,
      custom_headers: customHeaders,
    });
  }

  async listWebhookSubscriptions() {
    return this.get('/api/v1/webhooks/subscriptions');
  }

  async deleteWebhookSubscription(subscriptionId) {
    return this.delete(`/api/v1/webhooks/subscriptions/${encodeURIComponent(subscriptionId)}`);
  }

  async testWebhookSubscription(subscriptionId) {
    return this.post(`/api/v1/webhooks/subscriptions/${encodeURIComponent(subscriptionId)}/test`, {});
  }

  // 6. Cryptographic HMAC Verification
  static verifyWebhookSignature(rawPayload, signatureHeader, secretKey) {
    if (!signatureHeader || !secretKey) return false;
    const cleanHeader = signatureHeader.replace(/^sha256=/, '').trim();
    const computed = crypto
      .createHmac('sha256', secretKey)
      .update(typeof rawPayload === 'string' ? rawPayload : JSON.stringify(rawPayload))
      .digest('hex');

    try {
      return crypto.timingSafeEqual(Buffer.from(computed, 'utf8'), Buffer.from(cleanHeader, 'utf8'));
    } catch {
      return false;
    }
  }

  // Internal HTTP helper
  async request(method, path, body = null) {
    const url = `${this.baseUrl}/${path.replace(/^\/+/, '')}`;
    const headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': 'AiSalesCrm-JS-SDK/1.0',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      const text = await response.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { raw: text };
      }

      if (!response.ok) {
        const errorMsg = data.detail
          ? (typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail)
          : `HTTP ${response.status} Error`;
        throw new AiSalesCrmError(errorMsg, response.status, data);
      }

      return data;
    } catch (err) {
      if (err instanceof AiSalesCrmError) throw err;
      throw new AiSalesCrmError(`Network request failed: ${err.message}`);
    } finally {
      clearTimeout(timer);
    }
  }

  get(path) {
    return this.request('GET', path);
  }

  post(path, body) {
    return this.request('POST', path, body);
  }

  delete(path) {
    return this.request('DELETE', path);
  }
}

module.exports = {
  AiSalesCrm,
  AiSalesCrmError,
};
