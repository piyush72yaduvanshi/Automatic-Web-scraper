"""Phase 2 Native Python Automation, Deliverability, Marketing & Compliance Schema

Revision ID: 003
Revises: 002
Create Date: 2026-11-03 12:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update outreach_campaigns with campaign_type
    try:
        op.add_column('outreach_campaigns', sa.Column('campaign_type', sa.String(50), nullable=True, server_default='B2B_PROSPECTING'))
    except Exception:
        pass

    # 2. Workflow Definitions
    op.create_table(
        'workflow_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('trigger_type', sa.String(50), server_default='MANUAL', nullable=False),
        sa.Column('trigger_config', sa.Text(), nullable=True),
        sa.Column('input_schema', sa.Text(), nullable=True),
        sa.Column('steps_json', sa.Text(), nullable=False),
        sa.Column('retry_config', sa.Text(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), server_default='300', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_workflow_def_name', 'workflow_definitions', ['name'])
    op.create_index('idx_workflow_def_trigger', 'workflow_definitions', ['trigger_type'])

    # 3. Workflow Executions
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflow_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trigger_event', sa.String(50), server_default='MANUAL', nullable=False),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('current_step_id', sa.String(100), nullable=True),
        sa.Column('input_payload', sa.Text(), nullable=True),
        sa.Column('step_results', sa.Text(), nullable=True),
        sa.Column('error_info', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('completion_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_wf_exec_status', 'workflow_executions', ['status'])
    op.create_index('idx_wf_exec_workflow_id', 'workflow_executions', ['workflow_id'])

    # 4. Workflow Events
    op.create_table(
        'workflow_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('processed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_wf_event_type', 'workflow_events', ['event_type'])

    # 5. Email Accounts
    op.create_table(
        'email_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_address', sa.String(255), nullable=False, unique=True),
        sa.Column('provider', sa.String(50), server_default='GMAIL', nullable=False),
        sa.Column('oauth_status', sa.String(50), server_default='NOT_CONFIGURED', nullable=False),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('sending_permissions', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('daily_quota', sa.Integer(), server_default='50', nullable=False),
        sa.Column('sent_today', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_send_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('health_status', sa.String(50), server_default='HEALTHY', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_email_account_addr', 'email_accounts', ['email_address'])

    # 6. Email Domains
    op.create_table(
        'email_domains',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('domain_name', sa.String(255), nullable=False, unique=True),
        sa.Column('spf_status', sa.String(50), server_default='UNVERIFIED', nullable=False),
        sa.Column('dkim_status', sa.String(50), server_default='UNVERIFIED', nullable=False),
        sa.Column('dmarc_status', sa.String(50), server_default='UNVERIFIED', nullable=False),
        sa.Column('mx_status', sa.String(50), server_default='UNVERIFIED', nullable=False),
        sa.Column('dns_records_json', sa.Text(), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_email_domain_name', 'email_domains', ['domain_name'])

    # 7. Email Events
    op.create_table(
        'email_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_email_event_type', 'email_events', ['event_type'])
    op.create_index('idx_email_event_recipient', 'email_events', ['recipient'])

    # 8. Campaign Members
    op.create_table(
        'campaign_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), server_default='ENROLLED', nullable=False),
        sa.Column('current_step_number', sa.Integer(), server_default='0', nullable=False),
        sa.Column('next_step_due_at', sa.DateTime(), nullable=True),
        sa.Column('last_step_sent_at', sa.DateTime(), nullable=True),
        sa.Column('enrolled_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_camp_member_camp_id', 'campaign_members', ['campaign_id'])
    op.create_index('idx_camp_member_recipient', 'campaign_members', ['recipient_email'])

    # 9. Followup Sequences
    op.create_table(
        'followup_sequences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('campaign_type', sa.String(50), server_default='B2B_PROSPECTING', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('stop_on_reply', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('stop_on_meeting', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('stop_on_unsubscribe', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 10. Followup Steps
    op.create_table(
        'followup_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('sequence_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('followup_sequences.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('delay_days', sa.Integer(), server_default='0', nullable=False),
        sa.Column('channel', sa.String(50), server_default='EMAIL', nullable=False),
        sa.Column('subject_template', sa.String(500), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 11. Campaign Events
    op.create_table(
        'campaign_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 12. Consent Records
    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recipient', sa.String(255), nullable=False, unique=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source', sa.String(100), server_default='MANUAL', nullable=False),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('lawful_basis', sa.String(100), server_default='LEGITIMATE_INTEREST', nullable=False),
        sa.Column('channel_email_consent', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('channel_whatsapp_consent', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('marketing_eligible', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('compliance_notes', sa.Text(), nullable=True),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_consent_recipient', 'consent_records', ['recipient'])

    # 13. Data Deletion Requests
    op.create_table(
        'data_deletion_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('reason', sa.String(255), server_default='USER_REQUEST', nullable=False),
        sa.Column('status', sa.String(50), server_default='REQUESTED', nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('audit_notes', sa.Text(), nullable=True),
    )

    # 14. Content Items
    op.create_table(
        'content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('pillar', sa.String(100), server_default='TECHNICAL_EXPERTISE', nullable=False),
        sa.Column('target_audience', sa.String(255), nullable=True),
        sa.Column('platforms_json', sa.Text(), nullable=True),
        sa.Column('core_idea', sa.Text(), nullable=False),
        sa.Column('platform_drafts_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='DRAFT', nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # 15. Content Calendar Entries
    op.create_table(
        'content_calendar_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(50), server_default='SCHEDULED', nullable=False),
        sa.Column('publishing_provider_status', sa.String(50), server_default='NOT_CONFIGURED', nullable=False),
        sa.Column('external_post_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 16. SEO Projects
    op.create_table(
        'seo_projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('target_domain', sa.String(255), nullable=False),
        sa.Column('target_location', sa.String(100), server_default='National', nullable=False),
        sa.Column('gsc_connected', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 17. SEO Keywords
    op.create_table(
        'seo_keywords',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seo_projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('keyword', sa.String(255), nullable=False),
        sa.Column('cluster_name', sa.String(100), server_default='General', nullable=False),
        sa.Column('search_intent', sa.String(50), server_default='COMMERCIAL', nullable=False),
        sa.Column('search_volume', sa.Integer(), server_default='0', nullable=False),
        sa.Column('difficulty_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('target_page_type', sa.String(50), server_default='SERVICE_PAGE', nullable=False),
        sa.Column('content_brief', sa.Text(), nullable=True),
        sa.Column('meta_title', sa.String(255), nullable=True),
        sa.Column('meta_description', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), server_default='PLANNED', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 18. Paid Ad Reports
    op.create_table(
        'paid_ad_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('campaign_name', sa.String(255), nullable=False),
        sa.Column('spend_usd', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('impressions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('clicks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('conversions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('leads_attributed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('report_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 19. Community Discussions
    op.create_table(
        'community_discussions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('platform', sa.String(50), server_default='REDDIT', nullable=False),
        sa.Column('thread_title', sa.String(500), nullable=False),
        sa.Column('thread_url', sa.String(500), nullable=False),
        sa.Column('topic', sa.String(255), nullable=True),
        sa.Column('relevance_score', sa.Float(), server_default='0.8', nullable=False),
        sa.Column('draft_response', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='PENDING_REVIEW', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # 20. Report Snapshots
    op.create_table(
        'report_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('metrics_json', sa.Text(), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('recommendations_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_report_snap_type', 'report_snapshots', ['report_type'])


def downgrade() -> None:
    pass
