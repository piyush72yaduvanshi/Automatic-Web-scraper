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

// -------------------------------------------------------------
// Phase 2: Workflow Automation Engine (No n8n)
// -------------------------------------------------------------
export interface WorkflowDefinitionItem {
  id: string;
  name: string;
  description?: string;
  version: number;
  trigger_type: string;
  trigger_config?: Record<string, any>;
  steps: Array<{
    step_id: string;
    name: string;
    action_type: string;
    config?: Record<string, any>;
  }>;
  is_active: boolean;
  timeout_seconds: number;
  created_at?: string;
}

export interface WorkflowExecutionItem {
  id: string;
  workflow_id: string;
  workflow_name: string;
  trigger_event: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'RETRYING' | 'CANCELLED' | 'WAITING_FOR_APPROVAL';
  current_step_id?: string;
  retry_count: number;
  start_time?: string;
  completion_time?: string;
  error_info?: string;
  step_results?: Record<string, any>;
  created_at: string;
}

// -------------------------------------------------------------
// Phase 2: Deliverability & Mailbox Health
// -------------------------------------------------------------
export interface EmailAccountItem {
  id: string;
  email_address: string;
  provider: string;
  oauth_status: string;
  sending_permissions: boolean;
  daily_quota: number;
  sent_today: number;
  health_status: 'HEALTHY' | 'WARMING' | 'DEGRADED' | 'RESTRICTED';
  last_sync_at?: string;
  last_send_at?: string;
  last_error?: string;
}

export interface EmailDomainItem {
  id: string;
  domain_name: string;
  spf_status: string;
  dkim_status: string;
  dmarc_status: string;
  mx_status: string;
  dns_records?: Record<string, any>;
  last_checked_at?: string;
}

export interface DeliverabilityStats {
  kill_switch_active: boolean;
  total_sent: number;
  total_delivered: number;
  total_bounced: number;
  total_replied: number;
  total_unsubscribed: number;
  total_complaints: number;
  bounce_rate_percent: number;
  reply_rate_percent: number;
  mailbox_count: number;
  domain_count: number;
}

// -------------------------------------------------------------
// Phase 2: Follow-up Sequences & Campaigns
// -------------------------------------------------------------
export interface FollowupStepItem {
  step_number: number;
  delay_days: number;
  channel: string;
  subject_template?: string;
  body_template?: string;
}

export interface FollowupSequenceItem {
  id: string;
  name: string;
  description?: string;
  campaign_type: string;
  is_active: boolean;
  stop_on_reply: boolean;
  steps_count: number;
  steps: FollowupStepItem[];
}

export interface CampaignDetailedItem {
  id: string;
  name: string;
  description?: string;
  campaign_type: string;
  channel: string;
  status: string;
  total_members: number;
  active_members: number;
  sent_count: number;
  delivered_count: number;
  replied_count: number;
  bounced_count: number;
  created_at?: string;
}

// -------------------------------------------------------------
// Phase 2: Compliance & Consent
// -------------------------------------------------------------
export interface ConsentRecordItem {
  id: string;
  recipient: string;
  source: string;
  lawful_basis: string;
  channel_email_consent: boolean;
  channel_whatsapp_consent: boolean;
  marketing_eligible: boolean;
  compliance_notes?: string;
  collected_at?: string;
}

// -------------------------------------------------------------
// Phase 2: Content & SEO
// -------------------------------------------------------------
export interface ContentItemData {
  id: string;
  title: string;
  pillar: string;
  target_audience?: string;
  platforms: string[];
  core_idea: string;
  platform_drafts: Record<string, string>;
  status: string;
  published_at?: string;
  created_at?: string;
}

export interface CalendarEntryItem {
  id: string;
  content_item_id: string;
  content_title: string;
  pillar: string;
  channel: string;
  scheduled_for: string;
  status: string;
  publishing_provider_status: string;
}

export interface SEOProjectItem {
  id: string;
  name: string;
  target_domain: string;
  target_location: string;
  gsc_connected: boolean;
  keywords_count: number;
}

export interface SEOKeywordItem {
  id: string;
  keyword: string;
  cluster_name: string;
  search_intent: string;
  search_volume: number;
  difficulty_score: number;
  target_page_type: string;
  meta_title?: string;
  meta_description?: string;
  status: string;
}

// -------------------------------------------------------------
// Phase 2: Reports & Exceptions
// -------------------------------------------------------------
export interface ReportSnapshotItem {
  id: string;
  report_type: 'DAILY' | 'WEEKLY' | 'MONTHLY';
  period_start: string;
  period_end: string;
  executive_summary: string;
  metrics: Record<string, any>;
  recommendations: string[];
  created_at: string;
}

export interface ExceptionItem {
  id: string;
  category: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  title: string;
  details: string;
  entity_id: string;
  timestamp: string;
  action_type: string;
}

// -------------------------------------------------------------
// Social Media Automation Interfaces
// -------------------------------------------------------------
export interface SocialAccountItem {
  id: string;
  platform: 'INSTAGRAM' | 'FACEBOOK' | 'TWITTER' | 'LINKEDIN_PERSONAL' | 'LINKEDIN_ORG';
  account_name: string;
  account_handle: string;
  account_id?: string;
  status: 'ACTIVE' | 'NOT_CONFIGURED' | 'EXPIRED' | 'ERROR';
  followers_count: number;
  profile_image_url?: string;
  token_expires_at?: string;
  last_sync_at?: string;
}

export interface CreativeBrief {
  visual_concept?: string;
  aspect_ratio?: string;
  dimensions?: string;
  text_overlay?: string;
  color_palette?: string[];
}

export interface SocialPostItem {
  id: string;
  account_id?: string;
  platform: 'INSTAGRAM' | 'FACEBOOK' | 'TWITTER' | 'LINKEDIN_PERSONAL' | 'LINKEDIN_ORG';
  caption: string;
  hashtags: string[];
  media_urls: string[];
  creative_brief: CreativeBrief;
  automation_mode: 'MANUAL' | 'APPROVAL_BASED' | 'FULLY_AUTOMATED';
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'SCHEDULED' | 'PUBLISHING' | 'PUBLISHED' | 'FAILED' | 'CANCELLED';
  scheduled_for?: string;
  published_at?: string;
  external_post_id?: string;
  external_post_url?: string;
  publishing_provider_status: string;
  retry_count: number;
  last_error?: string;
  created_at: string;
}

export interface SocialAutomationRuleItem {
  id: string;
  name: string;
  mode: 'MANUAL' | 'APPROVAL_BASED' | 'FULLY_AUTOMATED';
  platforms: string[];
  pillars: string[];
  posting_times: string[];
  max_posts_per_day: number;
  is_active: boolean;
  last_run_at?: string;
}

export interface SocialAnalyticsData {
  summary: {
    total_posts: number;
    published_posts: number;
    scheduled_posts: number;
    draft_posts: number;
    total_impressions: number;
    total_reach: number;
    total_engagements: number;
    total_likes: number;
    total_comments: number;
    total_shares: number;
    total_clicks: number;
    average_engagement_rate: number;
  };
  platform_breakdown: Record<string, {
    post_count: number;
    impressions: number;
    engagements: number;
  }>;
  ai_executive_report: string;
}

export interface SocialResearchResult {
  trending_angles: string[];
  audience_resonances: string[];
  recommended_keywords: string[];
  visual_theme: string;
}


// -------------------------------------------------------------
// CRM Extended Interfaces: Call Logs, Notes, Emails
// -------------------------------------------------------------
export interface CallLogItem {
  id: string;
  contact_id?: string;
  company_id?: string;
  deal_id?: string;
  direction: 'INBOUND' | 'OUTBOUND';
  duration_seconds: number;
  phone_number?: string;
  recording_url?: string;
  transcript?: string;
  outcome?: string; // CONNECTED, NO_ANSWER, VOICEMAIL, BUSY
  notes?: string;
  call_started_at?: string;
  created_at: string;
  created_by?: string;
  company_name?: string;
  contact_name?: string;
}

export interface NoteItem {
  id: string;
  content: string;
  company_id?: string;
  contact_id?: string;
  deal_id?: string;
  lead_id?: string;
  is_pinned: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
  company_name?: string;
  contact_name?: string;
  deal_title?: string;
}

export interface EmailItem {
  id: string;
  contact_id?: string;
  company_id?: string;
  deal_id?: string;
  subject?: string;
  body_text?: string;
  body_html?: string;
  direction: 'INBOUND' | 'OUTBOUND';
  status: string; // draft, sent, delivered, opened, clicked, replied, bounced
  opened_at?: string;
  clicked_at?: string;
  replied_at?: string;
  sent_at?: string;
  created_at: string;
  company_name?: string;
  contact_name?: string;
}

