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
  qualification_score?: number;
  qualification_status?: string;
  qualification_reasoning?: string;
  data_confidence_score?: number;
  company_id?: string;
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
  company_research?: string;
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

// -------------------------------------------------------------
// CRM Interfaces
// -------------------------------------------------------------
export interface CompanyItem {
  id: string;
  name: string;
  domain?: string;
  website?: string;
  industry?: string;
  size_range?: string;
  location?: string;
  status: string;
  deals_count: number;
  contacts_count: number;
  created_at: string;
}

export interface ContactItem {
  id: string;
  company_id?: string;
  company_name?: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  job_title?: string;
  department?: string;
  linkedin_url?: string;
  is_decision_maker: boolean;
  reachability_status: string;
  created_at: string;
}

export interface DealItem {
  id: string;
  title: string;
  company_name: string;
  contact_name?: string;
  amount: number;
  currency: string;
  status: string;
  stage?: string;
  probability: number;
  created_at: string;
}

export interface KanbanStage {
  id: string;
  name: string;
  order: number;
  probability: number;
  total_value: number;
  deals_count: number;
  deals: DealItem[];
}

export interface KanbanBoard {
  pipeline_id: string;
  pipeline_name: string;
  stages: KanbanStage[];
}

export interface ActivityItem {
  id: string;
  activity_type: string;
  title: string;
  description?: string;
  company_name?: string;
  created_at: string;
}

export interface TaskItem {
  id: string;
  title: string;
  description?: string;
  due_date?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  company_name?: string;
  created_at: string;
}

export interface MeetingItem {
  id: string;
  title: string;
  company_name?: string;
  start_time: string;
  end_time: string;
  agenda?: string;
  status: string;
  prep_notes?: string;
}

// -------------------------------------------------------------
// Outreach Interfaces
// -------------------------------------------------------------
export interface OutreachApprovalItem {
  id: string;
  action_type: string;
  recipient_name: string;
  recipient_destination: string;
  subject?: string;
  body_content: string;
  evidence_context?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'SENT' | 'FAILED';
  rejection_reason?: string;
  error_message?: string;
  created_at: string;
  sent_at?: string;
}

export interface CampaignItem {
  id: string;
  name: string;
  channel: string;
  status: string;
  total_prospects: number;
  sent_count: number;
  replied_count: number;
  steps_count: number;
  created_at: string;
}

export interface ConversationItem {
  id: string;
  channel: string;
  subject?: string;
  status: string;
  last_message_at: string;
  messages_count: number;
}

export interface MessageItem {
  id: string;
  direction: 'INBOUND' | 'OUTBOUND';
  sender: string;
  recipient: string;
  body: string;
  delivery_status: string;
  ai_classification?: string;
  suggested_reply?: string;
  created_at: string;
}

// -------------------------------------------------------------
// AI Agents & Orchestration Interfaces
// -------------------------------------------------------------
export interface AgentDefinition {
  name: string;
  role: string;
  description: string;
  allowed_tools: string[];
  max_execution_steps: number;
}

export interface AgentRunItem {
  id: string;
  agent_name: string;
  task_type: string;
  status: string;
  duration_ms: number;
  error_message?: string;
  created_at: string;
}

// -------------------------------------------------------------
// Knowledge & Integrations Interfaces
// -------------------------------------------------------------
export interface KnowledgeDocItem {
  id: string;
  title: string;
  category: string;
  chunks_count: number;
  created_at: string;
}

export interface IntegrationStatusItem {
  name: string;
  display_name: string;
  category: string;
  description: string;
  status: string;
  is_configured: boolean;
  is_enabled: boolean;
  last_checked_at?: string;
  last_success_at?: string;
  last_error?: string;
  user_message: string;
}

export interface HealthSummary {
  overall_status: string;
  total_integrations: number;
  healthy_count: number;
  not_configured_count: number;
  degraded_count: number;
  disabled_count: number;
  integrations: IntegrationStatusItem[];
}
