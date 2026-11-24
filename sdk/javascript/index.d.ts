export interface DiscoveredLead {
  business_name: string;
  phone?: string;
  email?: string;
  website?: string;
  address?: string;
  city?: string;
  state?: string;
  rating?: number;
  reviews_count?: number;
}

export interface IngestLeadPayload {
  business_name: string;
  category?: string;
  email?: string;
  phone?: string;
  website?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  source_provider?: string;
  external_id?: string;
  is_verified?: boolean;
}

export class AiSalesCrmError extends Error {
  statusCode?: number | null;
  responseBody?: any;
}

export class AiSalesCrm {
  constructor(options?: { baseUrl?: string; apiKey?: string | null; timeout?: number });
  discoverLeads(params: { query: string; location: string; limit?: number; provider?: string }): Promise<any>;
  getLead(leadId: string): Promise<any>;
  listLeads(params?: { page?: number; pageSize?: number; status?: string | null }): Promise<any>;
  ingestLead(leadData: IngestLeadPayload): Promise<any>;
  qualifyLead(leadId: string): Promise<any>;
  enrichLead(leadId: string): Promise<any>;
  sendOutreachEmail(params: { leadId: string; subject: string; body?: string | null }): Promise<any>;
  createWebhookSubscription(params: { name: string; targetUrl: string; events?: string[]; customHeaders?: Record<string, string> }): Promise<any>;
  listWebhookSubscriptions(): Promise<any[]>;
  deleteWebhookSubscription(subscriptionId: string): Promise<boolean>;
  testWebhookSubscription(subscriptionId: string): Promise<any>;
  static verifyWebhookSignature(rawPayload: string | Buffer | object, signatureHeader: string, secretKey: string): boolean;
}
