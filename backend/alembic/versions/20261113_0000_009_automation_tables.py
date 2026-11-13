"""Add automation_settings and lead_exceptions tables

Revision ID: 009_automation_tables
Revises: 20261112_0000_008_crm_call_logs_notes_emails
Create Date: 2026-11-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '009_automation_tables'
down_revision = '20261112_0000_008_crm_call_logs_notes_emails'
branch_labels = None
depends_on = None


def upgrade():
    # Create automation_settings table
    op.create_table(
        'automation_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('setting_key', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('setting_value', sa.Text, nullable=False),
        sa.Column('data_type', sa.String(20), default='boolean'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )
    
    # Create lead_exceptions table
    op.create_table(
        'lead_exceptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('lead_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('exception_type', sa.String(100), nullable=False, index=True),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('severity', sa.String(20), default='warning', index=True),
        sa.Column('resolved', sa.Boolean, default=False, index=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow, nullable=False, index=True),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
    )
    
    # Create composite indexes
    op.create_index('idx_exception_lead_type', 'lead_exceptions', ['lead_id', 'exception_type'])
    op.create_index('idx_exception_severity_resolved', 'lead_exceptions', ['severity', 'resolved'])
    
    # Add automation tracking columns to business_leads
    op.add_column('business_leads', sa.Column('outreach_enrolled', sa.Boolean, default=False, server_default='false'))
    op.add_column('business_leads', sa.Column('outreach_enrollment_date', sa.DateTime, nullable=True))
    op.add_column('business_leads', sa.Column('crm_converted', sa.Boolean, default=False, server_default='false'))
    op.add_column('business_leads', sa.Column('crm_conversion_date', sa.DateTime, nullable=True))
    op.add_column('business_leads', sa.Column('email_enrichment_status', sa.String(50), default='pending', server_default='pending'))
    op.add_column('business_leads', sa.Column('last_automation_run', sa.DateTime, nullable=True))
    
    # Create indexes on new columns
    op.create_index('idx_outreach_enrolled', 'business_leads', ['outreach_enrolled'])
    op.create_index('idx_crm_converted', 'business_leads', ['crm_converted'])
    
    # Seed default automation settings
    op.execute("""
        INSERT INTO automation_settings (id, setting_key, setting_value, data_type, description) VALUES
        (gen_random_uuid(), 'auto_enroll_to_outreach', 'true', 'boolean', 'Automatically enroll qualified leads in outreach sequences'),
        (gen_random_uuid(), 'auto_approve_emails', 'true', 'boolean', 'Automatically approve AI-generated outreach emails'),
        (gen_random_uuid(), 'auto_convert_to_crm', 'true', 'boolean', 'Automatically convert qualified leads to CRM companies/contacts/deals'),
        (gen_random_uuid(), 'min_score_for_outreach', '70', 'integer', 'Minimum qualification score required for automatic outreach enrollment'),
        (gen_random_uuid(), 'min_score_for_crm', '60', 'integer', 'Minimum qualification score required for automatic CRM conversion'),
        (gen_random_uuid(), 'email_enrichment_enabled', 'true', 'boolean', 'Enable automatic email enrichment for leads without email'),
        (gen_random_uuid(), 'bulk_processing_batch_size', '50', 'integer', 'Number of leads to process in each batch')
    """)


def downgrade():
    # Drop indexes
    op.drop_index('idx_crm_converted', 'business_leads')
    op.drop_index('idx_outreach_enrolled', 'business_leads')
    
    # Drop columns from business_leads
    op.drop_column('business_leads', 'last_automation_run')
    op.drop_column('business_leads', 'email_enrichment_status')
    op.drop_column('business_leads', 'crm_conversion_date')
    op.drop_column('business_leads', 'crm_converted')
    op.drop_column('business_leads', 'outreach_enrollment_date')
    op.drop_column('business_leads', 'outreach_enrolled')
    
    # Drop tables
    op.drop_table('lead_exceptions')
    op.drop_table('automation_settings')
