"""Social and Inbound Lead Capture System

Revision ID: 005
Revises: 004
Create Date: 2026-11-03 18:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add lead_source column to business_leads table
    op.add_column(
        'business_leads',
        sa.Column('lead_source', sa.String(50), nullable=True, server_default='DISCOVERY')
    )
    op.add_column(
        'business_leads',
        sa.Column('social_engagement_count', sa.Integer(), nullable=True, server_default='0')
    )
    op.add_column(
        'business_leads',
        sa.Column('last_social_engagement_at', sa.DateTime(), nullable=True)
    )
    
    # Create index on lead_source
    op.create_index('idx_business_leads_source', 'business_leads', ['lead_source'])
    
    # Backfill existing leads with DISCOVERY source
    op.execute("UPDATE business_leads SET lead_source = 'DISCOVERY' WHERE lead_source IS NULL")
    
    # 2. Create social_media_leads table
    op.create_table(
        'social_media_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_leads.id', ondelete='SET NULL'), nullable=True),
        
        # Platform Information
        sa.Column('platform', sa.String(50), nullable=False),  # INSTAGRAM, FACEBOOK, TWITTER, LINKEDIN
        sa.Column('social_profile_url', sa.String(500), nullable=False),
        sa.Column('social_username', sa.String(200), nullable=False),
        
        # Engagement Data
        sa.Column('message_content', sa.Text(), nullable=True),
        sa.Column('engagement_type', sa.String(100), nullable=False),  # COMMENT, DM, MENTION, etc.
        sa.Column('engagement_url', sa.String(500), nullable=True),
        
        # Lead Context
        sa.Column('post_context', sa.Text(), nullable=True),
        sa.Column('sentiment', sa.String(50), nullable=True),
        sa.Column('interest_score', sa.Float(), nullable=True, server_default='0.5'),
        
        # Processing
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processing_notes', sa.Text(), nullable=True),
        
        # Metadata
        sa.Column('platform_user_id', sa.String(255), nullable=True),
        sa.Column('engagement_timestamp', sa.DateTime(), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for social_media_leads
    op.create_index('idx_social_media_platform', 'social_media_leads', ['platform'])
    op.create_index('idx_social_media_processed', 'social_media_leads', ['processed'])
    op.create_index('idx_social_media_username', 'social_media_leads', ['social_username'])
    op.create_index('idx_social_media_timestamp', 'social_media_leads', ['engagement_timestamp'])
    op.create_index('idx_social_media_lead_id', 'social_media_leads', ['lead_id'])
    op.create_unique_constraint(
        'uq_social_media_dedup',
        'social_media_leads',
        ['platform', 'platform_user_id', 'engagement_type', 'engagement_timestamp']
    )
    
    # 3. Create inbound_messages table
    op.create_table(
        'inbound_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('business_leads.id', ondelete='SET NULL'), nullable=True),
        
        # Channel Information
        sa.Column('channel', sa.String(50), nullable=False),  # EMAIL, WHATSAPP, SMS
        sa.Column('sender_contact', sa.String(255), nullable=False),
        
        # Message Content
        sa.Column('message_body', sa.Text(), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        
        # Lead Intelligence
        sa.Column('interest_score', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('sentiment', sa.String(50), nullable=True),
        sa.Column('classification', sa.String(100), nullable=True),  # INTERESTED, OBJECTION, NOT_NOW, etc.
        sa.Column('suggested_reply', sa.Text(), nullable=True),
        
        # Context
        sa.Column('thread_id', sa.String(255), nullable=True),
        sa.Column('in_reply_to_message_id', sa.String(255), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Processing
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_human_attention', sa.Boolean(), nullable=False, server_default='false'),
        
        # Metadata
        sa.Column('message_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('platform_message_id', sa.String(255), nullable=True),
        
        # Audit
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for inbound_messages
    op.create_index('idx_inbound_channel', 'inbound_messages', ['channel'])
    op.create_index('idx_inbound_sender', 'inbound_messages', ['sender_contact'])
    op.create_index('idx_inbound_processed', 'inbound_messages', ['processed'])
    op.create_index('idx_inbound_classification', 'inbound_messages', ['classification'])
    op.create_index('idx_inbound_received', 'inbound_messages', ['received_at'])
    op.create_index('idx_inbound_thread', 'inbound_messages', ['thread_id'])
    op.create_unique_constraint(
        'uq_inbound_dedup',
        'inbound_messages',
        ['channel', 'platform_message_id']
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('inbound_messages')
    op.drop_table('social_media_leads')
    
    # Drop columns from business_leads
    op.drop_index('idx_business_leads_source', 'business_leads')
    op.drop_column('business_leads', 'last_social_engagement_at')
    op.drop_column('business_leads', 'social_engagement_count')
    op.drop_column('business_leads', 'lead_source')
