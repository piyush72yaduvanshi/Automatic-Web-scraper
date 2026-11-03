"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create business_leads table
    op.create_table(
        'business_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_name', sa.String(500), nullable=False),
        sa.Column('category', sa.String(200)),
        sa.Column('description', sa.Text()),
        sa.Column('address', sa.Text()),
        sa.Column('city', sa.String(200)),
        sa.Column('state', sa.String(200)),
        sa.Column('country', sa.String(100)),
        sa.Column('website', sa.String(500)),
        sa.Column('source_provider', sa.String(100), nullable=False),
        sa.Column('provider_external_id', sa.String(500), unique=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='discovered'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for business_leads
    op.create_index('idx_business_name', 'business_leads', ['business_name'])
    op.create_index('idx_category', 'business_leads', ['category'])
    op.create_index('idx_city', 'business_leads', ['city'])
    op.create_index('idx_state', 'business_leads', ['state'])
    op.create_index('idx_country', 'business_leads', ['country'])
    op.create_index('idx_website', 'business_leads', ['website'])
    op.create_index('idx_status', 'business_leads', ['status'])
    op.create_index('idx_created_at', 'business_leads', ['created_at'])
    op.create_index('idx_business_name_city', 'business_leads', ['business_name', 'city'])
    op.create_index('idx_category_city', 'business_leads', ['category', 'city'])
    
    # Create lead_contacts table
    op.create_table(
        'lead_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contact_type', sa.Enum('PHONE', 'EMAIL', name='contacttype'), nullable=False),
        sa.Column('original_value', sa.String(500), nullable=False),
        sa.Column('normalized_value', sa.String(500)),
        sa.Column('verification_status', sa.String(50), server_default='unverified'),
        sa.Column('source_url', sa.Text()),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['business_leads.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for lead_contacts
    op.create_index('idx_lead_contact_lead_id', 'lead_contacts', ['lead_id'])
    op.create_index('idx_normalized_value', 'lead_contacts', ['normalized_value'])
    op.create_index('idx_lead_contact_type', 'lead_contacts', ['lead_id', 'contact_type'])
    
    # Create lead_social_profiles table
    op.create_table(
        'lead_social_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.Enum('INSTAGRAM', 'LINKEDIN', 'FACEBOOK', 'X', name='socialplatform'), nullable=False),
        sa.Column('profile_url', sa.String(500), nullable=False),
        sa.Column('verification_status', sa.String(50), server_default='unverified'),
        sa.Column('source_url', sa.Text()),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['business_leads.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for lead_social_profiles
    op.create_index('idx_social_lead_id', 'lead_social_profiles', ['lead_id'])
    op.create_index('idx_profile_url', 'lead_social_profiles', ['profile_url'])
    op.create_index('idx_lead_platform', 'lead_social_profiles', ['lead_id', 'platform'])
    
    # Create discovery_jobs table
    op.create_table(
        'discovery_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('search_query', sa.String(500), nullable=False),
        sa.Column('location', sa.String(500), nullable=False),
        sa.Column('radius_km', sa.Float()),
        sa.Column('requested_limit', sa.Integer(), server_default='50'),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('provider_job_id', sa.String(500)),
        sa.Column('status', sa.Enum('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', name='jobstatus'), nullable=False, server_default='QUEUED'),
        sa.Column('total_found', sa.Integer(), server_default='0'),
        sa.Column('total_enriched', sa.Integer(), server_default='0'),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
    )
    
    # Create indexes for discovery_jobs
    op.create_index('idx_status_created', 'discovery_jobs', ['status', 'created_at'])
    op.create_index('idx_provider_job', 'discovery_jobs', ['provider', 'provider_job_id'])
    
    # Create lead_source_evidence table
    op.create_table(
        'lead_source_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('extracted_value', sa.Text(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('provider', sa.String(100)),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['business_leads.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for lead_source_evidence
    op.create_index('idx_evidence_lead_id', 'lead_source_evidence', ['lead_id'])
    op.create_index('idx_lead_field', 'lead_source_evidence', ['lead_id', 'field_name'])


def downgrade() -> None:
    op.drop_table('lead_source_evidence')
    op.drop_table('discovery_jobs')
    op.drop_table('lead_social_profiles')
    op.drop_table('lead_contacts')
    op.drop_table('business_leads')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS contacttype')
    op.execute('DROP TYPE IF EXISTS socialplatform')
    op.execute('DROP TYPE IF EXISTS jobstatus')
