"""crm ai operating system schema

Revision ID: 002
Revises: 001
Create Date: 2026-11-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update business_leads with qualification fields
    try:
        op.add_column('business_leads', sa.Column('qualification_score', sa.Float(), nullable=True, server_default='50.0'))
        op.add_column('business_leads', sa.Column('qualification_status', sa.String(50), nullable=True, server_default='New'))
        op.add_column('business_leads', sa.Column('qualification_reasoning', sa.Text(), nullable=True))
        op.add_column('business_leads', sa.Column('qualification_breakdown', sa.Text(), nullable=True))
        op.add_column('business_leads', sa.Column('company_research', sa.Text(), nullable=True))
        op.add_column('business_leads', sa.Column('data_confidence_score', sa.Float(), nullable=True, server_default='50.0'))
        op.add_column('business_leads', sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True))
    except Exception:
        pass

    # 2. Companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('industry', sa.String(200), nullable=True),
        sa.Column('size_range', sa.String(50), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tech_stack', sa.Text(), nullable=True),
        sa.Column('annual_revenue', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), server_default='active', nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_companies_name', 'companies', ['name'])
    op.create_index('idx_companies_domain', 'companies', ['domain'])
    op.create_index('idx_companies_industry', 'companies', ['industry'])
    op.create_index('idx_companies_status', 'companies', ['status'])

    # 3. Contacts table
    op.create_table(
        'contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), server_default='', nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(100), nullable=True),
        sa.Column('job_title', sa.String(200), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('is_decision_maker', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('reachability_status', sa.String(50), server_default='unverified', nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_contacts_email', 'contacts', ['email'])
    op.create_index('idx_contacts_company_id', 'contacts', ['company_id'])

    # 4. Pipelines & Stages
    op.create_table(
        'pipelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'pipeline_stages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('stage_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('probability', sa.Float(), server_default='0.2', nullable=False),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_stages_pipeline_id', 'pipeline_stages', ['pipeline_id'])

    # 5. Deals
    op.create_table(
        'deals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stage_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('currency', sa.String(10), server_default='USD', nullable=False),
        sa.Column('status', sa.String(50), server_default='open', nullable=False),
        sa.Column('probability', sa.Float(), server_default='0.2', nullable=False),
        sa.Column('expected_close_date', sa.DateTime(), nullable=True),
        sa.Column('lost_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['stage_id'], ['pipeline_stages.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_deals_company_id', 'deals', ['company_id'])
    op.create_index('idx_deals_stage_id', 'deals', ['stage_id'])
    op.create_index('idx_deals_status', 'deals', ['status'])

    # 6. Activities, Tasks, Meetings
    op.create_table(
        'activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('activity_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'crm_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.String(20), server_default='medium', nullable=False),
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_entity_type', sa.String(50), nullable=True),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'meetings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('agenda', sa.Text(), nullable=True),
        sa.Column('meeting_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), server_default='scheduled', nullable=False),
        sa.Column('prep_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
    )

    # 7. Outreach Campaigns, Steps, Approvals, Conversations
    op.create_table(
        'outreach_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('channel', sa.String(50), server_default='EMAIL', nullable=False),
        sa.Column('status', sa.String(50), server_default='DRAFT', nullable=False),
        sa.Column('target_audience_filters', sa.Text(), nullable=True),
        sa.Column('total_prospects', sa.Integer(), server_default='0', nullable=False),
        sa.Column('sent_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('delivered_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('opened_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('replied_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('bounced_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'campaign_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('delay_days', sa.Integer(), server_default='0', nullable=False),
        sa.Column('template_subject', sa.String(500), nullable=True),
        sa.Column('template_body', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(50), server_default='EMAIL', nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['outreach_campaigns.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'outreach_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action_type', sa.String(50), server_default='SEND_EMAIL', nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient_name', sa.String(200), server_default='Valued Prospect', nullable=False),
        sa.Column('recipient_destination', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body_content', sa.Text(), nullable=False),
        sa.Column('evidence_context', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['outreach_campaigns.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_approvals_status', 'outreach_approvals', ['status'])

    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('channel', sa.String(50), server_default='EMAIL', nullable=False),
        sa.Column('external_thread_id', sa.String(255), nullable=True),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), server_default='ACTIVE', nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('direction', sa.String(20), server_default='OUTBOUND', nullable=False),
        sa.Column('sender', sa.String(255), nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(50), server_default='text', nullable=False),
        sa.Column('delivery_status', sa.String(50), server_default='sent', nullable=False),
        sa.Column('ai_classification', sa.String(100), nullable=True),
        sa.Column('suggested_reply', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'suppression_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recipient', sa.String(255), nullable=False, unique=True),
        sa.Column('channel', sa.String(50), server_default='ALL', nullable=False),
        sa.Column('reason', sa.String(100), server_default='UNSUBSCRIBE', nullable=False),
        sa.Column('opted_out_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_suppression_recipient', 'suppression_records', ['recipient'])

    # 8. AI Orchestration, Knowledge, Memory & Audit
    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_name', sa.String(100), nullable=False),
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('input_parameters', sa.Text(), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_steps', sa.Text(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=False),
        sa.Column('estimated_cost_usd', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('duration_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_agent_runs_name', 'agent_runs', ['agent_name'])

    op.create_table(
        'knowledge_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), server_default='SERVICE_OFFERING', nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('file_type', sa.String(50), server_default='text', nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'knowledge_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), server_default='0', nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding_json', sa.Text(), nullable=True),
        sa.Column('token_count', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'memory_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(255), nullable=True),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('source', sa.String(100), server_default='user', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_memory_entity', 'memory_records', ['entity_type', 'entity_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(255), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('memory_records')
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')
    op.drop_table('agent_runs')
    op.drop_table('suppression_records')
    op.drop_table('conversation_messages')
    op.drop_table('conversations')
    op.drop_table('outreach_approvals')
    op.drop_table('campaign_steps')
    op.drop_table('outreach_campaigns')
    op.drop_table('meetings')
    op.drop_table('crm_tasks')
    op.drop_table('activities')
    op.drop_table('deals')
    op.drop_table('pipeline_stages')
    op.drop_table('pipelines')
    op.drop_table('contacts')
    op.drop_table('companies')
