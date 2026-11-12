"""crm call logs notes emails tables

Revision ID: 008
Revises: 007
Create Date: 2026-11-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create call_logs, notes, and emails tables, and enhance existing tables."""
    
    # 1. Create call_logs table
    op.create_table(
        'call_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('direction', sa.String(20), nullable=False),  # INBOUND, OUTBOUND
        sa.Column('duration_seconds', sa.Integer(), server_default='0', nullable=False),
        sa.Column('phone_number', sa.String(100), nullable=True),
        sa.Column('recording_url', sa.String(500), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=True),  # CONNECTED, NO_ANSWER, VOICEMAIL, BUSY
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('call_started_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_call_logs_contact_id', 'call_logs', ['contact_id'])
    op.create_index('idx_call_logs_company_id', 'call_logs', ['company_id'])
    op.create_index('idx_call_logs_deal_id', 'call_logs', ['deal_id'])
    op.create_index('idx_call_logs_direction', 'call_logs', ['direction'])
    op.create_index('idx_call_logs_phone_number', 'call_logs', ['phone_number'])
    op.create_index('idx_call_logs_created_at', 'call_logs', ['created_at'])
    op.create_index('idx_call_logs_call_started_at', 'call_logs', ['call_started_at'])

    # 2. Create notes table
    op.create_table(
        'notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_id'], ['business_leads.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_notes_contact_id', 'notes', ['contact_id'])
    op.create_index('idx_notes_company_id', 'notes', ['company_id'])
    op.create_index('idx_notes_deal_id', 'notes', ['deal_id'])
    op.create_index('idx_notes_lead_id', 'notes', ['lead_id'])
    op.create_index('idx_notes_created_at', 'notes', ['created_at'])
    op.create_index('idx_notes_is_pinned', 'notes', ['is_pinned'])

    # 3. Create emails table
    op.create_table(
        'emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('direction', sa.String(20), nullable=False),  # INBOUND, OUTBOUND
        sa.Column('status', sa.String(50), server_default='draft', nullable=False),  # draft, sent, delivered, opened, clicked, replied, bounced
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('replied_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_emails_contact_id', 'emails', ['contact_id'])
    op.create_index('idx_emails_company_id', 'emails', ['company_id'])
    op.create_index('idx_emails_deal_id', 'emails', ['deal_id'])
    op.create_index('idx_emails_direction', 'emails', ['direction'])
    op.create_index('idx_emails_status', 'emails', ['status'])
    op.create_index('idx_emails_sent_at', 'emails', ['sent_at'])
    op.create_index('idx_emails_created_at', 'emails', ['created_at'])

    # 4. Enhance pipeline_stages table
    op.add_column('pipeline_stages', sa.Column('is_closed_won', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('pipeline_stages', sa.Column('is_closed_lost', sa.Boolean(), server_default='false', nullable=False))

    # 5. Enhance crm_tasks table
    op.add_column('crm_tasks', sa.Column('contact_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('crm_tasks', sa.Column('deal_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('crm_tasks', sa.Column('assigned_to', sa.String(100), nullable=True))
    
    op.create_foreign_key('fk_crm_tasks_contact_id', 'crm_tasks', 'contacts', ['contact_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_crm_tasks_deal_id', 'crm_tasks', 'deals', ['deal_id'], ['id'], ondelete='SET NULL')
    op.create_index('idx_crm_tasks_contact_id', 'crm_tasks', ['contact_id'])
    op.create_index('idx_crm_tasks_deal_id', 'crm_tasks', ['deal_id'])


def downgrade() -> None:
    """Reverse the migration."""
    
    # Drop indexes and columns from crm_tasks
    op.drop_index('idx_crm_tasks_deal_id', 'crm_tasks')
    op.drop_index('idx_crm_tasks_contact_id', 'crm_tasks')
    op.drop_constraint('fk_crm_tasks_deal_id', 'crm_tasks', type_='foreignkey')
    op.drop_constraint('fk_crm_tasks_contact_id', 'crm_tasks', type_='foreignkey')
    op.drop_column('crm_tasks', 'assigned_to')
    op.drop_column('crm_tasks', 'deal_id')
    op.drop_column('crm_tasks', 'contact_id')

    # Drop columns from pipeline_stages
    op.drop_column('pipeline_stages', 'is_closed_lost')
    op.drop_column('pipeline_stages', 'is_closed_won')

    # Drop emails table
    op.drop_index('idx_emails_created_at', 'emails')
    op.drop_index('idx_emails_sent_at', 'emails')
    op.drop_index('idx_emails_status', 'emails')
    op.drop_index('idx_emails_direction', 'emails')
    op.drop_index('idx_emails_deal_id', 'emails')
    op.drop_index('idx_emails_company_id', 'emails')
    op.drop_index('idx_emails_contact_id', 'emails')
    op.drop_table('emails')

    # Drop notes table
    op.drop_index('idx_notes_is_pinned', 'notes')
    op.drop_index('idx_notes_created_at', 'notes')
    op.drop_index('idx_notes_lead_id', 'notes')
    op.drop_index('idx_notes_deal_id', 'notes')
    op.drop_index('idx_notes_company_id', 'notes')
    op.drop_index('idx_notes_contact_id', 'notes')
    op.drop_table('notes')

    # Drop call_logs table
    op.drop_index('idx_call_logs_call_started_at', 'call_logs')
    op.drop_index('idx_call_logs_created_at', 'call_logs')
    op.drop_index('idx_call_logs_phone_number', 'call_logs')
    op.drop_index('idx_call_logs_direction', 'call_logs')
    op.drop_index('idx_call_logs_deal_id', 'call_logs')
    op.drop_index('idx_call_logs_company_id', 'call_logs')
    op.drop_index('idx_call_logs_contact_id', 'call_logs')
    op.drop_table('call_logs')
