export type JobStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type ContactType = 'EMAIL' | 'PHONE';

export type SocialPlatform = 'INSTAGRAM' | 'LINKEDIN' | 'FACEBOOK' | 'X';

export interface BusinessLead {
  id: string;
  business_name: string;
  category?: string;
  description?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  website?: string;
  source_provider: string;
  status: string;
  email_count?: number;
  phone_count?: number;
  social_count?: number;
  quality_score?: number;
  created_at: string;
  updated_at: string;
}

export interface LeadContact {
  id: string;
  contact_type: ContactType;
  original_value: string;
  normalized_value?: string;
  verification_status: string;
  source_url?: string;
  collected_at: string;
}

export interface LeadSocialProfile {
  id: string;
  platform: SocialPlatform;
  profile_url: string;
  verification_status: string;
  source_url?: string;
  collected_at: string;
}

export interface LeadSourceEvidence {
  id: string;
  field_name: string;
  extracted_value: string;
  source_url: string;
  provider?: string;
  collected_at: string;
}

export interface LeadDetail extends BusinessLead {
  contacts: LeadContact[];
  social_profiles: LeadSocialProfile[];
  source_evidence?: LeadSourceEvidence[];
  key_people?: { name: string; role: string }[];
  sources_consulted?: string[];
}

export interface LiveScannedLead {
  id: string;
  business_name: string;
  category?: string;
  description?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  website?: string;
  source_provider: string;
  email_count: number;
  phone_count: number;
  social_count: number;
  emails: { email: string; label?: string; verification_status?: string }[];
  phones: { original?: string; normalized?: string; label?: string }[];
  social_profiles: { platform: string; url: string }[];
  quality_score: number;
  sources_consulted?: string[];
  key_people?: { name: string; role: string }[];
}

export interface DiscoveryJob {
  id: string;
  search_query: string;
  location: string;
  radius_km?: number;
  requested_limit: number;
  provider: string;
  provider_job_id?: string;
  status: JobStatus;
  total_found: number;
  total_enriched: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface DiscoveryJobCreate {
  query: string;
  location: string;
  radius_km?: number;
  limit?: number;
  sources?: string[];
  enrich_emails?: boolean;
  enrich_phones?: boolean;
  enrich_socials?: boolean;
  preferred_provider?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Stats {
  total_leads: number;
  total_jobs: number;
  emails_found: number;
  phones_found: number;
  social_profiles_found: number;
  jobs_completed: number;
  jobs_failed: number;
  jobs_running: number;
}
