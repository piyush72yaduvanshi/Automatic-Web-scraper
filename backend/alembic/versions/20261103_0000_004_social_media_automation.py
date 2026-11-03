"""Social Media Automation Schema

Revision ID: 004
Revises: 003
Create Date: 2026-11-03 16:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. social_accounts
    op.create_table(
        'social_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        sa.Column('account_handle', sa.String(255), nullable=False),
        sa.Column('account_id', sa.String(255), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, server_default='NOT_CONFIGURED'),
        sa.Column('followers_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('profile_image_url', sa.String(500), nullable=True),
        sa.Column('account_metadata_json', sa.Text(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_social_accounts_platform', 'social_accounts', ['platform'])
    op.create_index('ix_social_accounts_status', 'social_accounts', ['status'])

    # 2. social_posts
    op.create_table(
        'social_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('content_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('social_accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('caption', sa.Text(), nullable=False),
        sa.Column('hashtags_json', sa.Text(), nullable=True),
        sa.Column('media_urls_json', sa.Text(), nullable=True),
        sa.Column('creative_brief_json', sa.Text(), nullable=True),
        sa.Column('automation_mode', sa.String(50), nullable=True, server_default='APPROVAL_BASED'),
        sa.Column('status', sa.String(50), nullable=True, server_default='DRAFT'),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('external_post_id', sa.String(255), nullable=True),
        sa.Column('external_post_url', sa.String(500), nullable=True),
        sa.Column('publishing_provider_status', sa.String(50), nullable=True, server_default='NOT_CONFIGURED'),
        sa.Column('api_response_json', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_social_posts_platform', 'social_posts', ['platform'])
    op.create_index('ix_social_posts_status', 'social_posts', ['status'])
    op.create_index('ix_social_posts_scheduled_for', 'social_posts', ['scheduled_for'])
    op.create_index('ix_social_posts_content_hash', 'social_posts', ['content_hash'])

    # 3. social_automation_rules
    op.create_table(
        'social_automation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('mode', sa.String(50), nullable=True, server_default='APPROVAL_BASED'),
        sa.Column('platforms_json', sa.Text(), nullable=False),
        sa.Column('pillars_json', sa.Text(), nullable=True),
        sa.Column('posting_times_json', sa.Text(), nullable=True),
        sa.Column('max_posts_per_day', sa.Integer(), nullable=True, server_default='2'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_social_automation_rules_mode', 'social_automation_rules', ['mode'])
    op.create_index('ix_social_automation_rules_is_active', 'social_automation_rules', ['is_active'])

    # 4. social_post_metrics
    op.create_table(
        'social_post_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('social_posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('reach', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('engagement_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('likes', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('comments', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('shares', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('clicks', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('engagement_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('fetched_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_social_post_metrics_post_id', 'social_post_metrics', ['post_id'])


def downgrade() -> None:
    op.drop_table('social_post_metrics')
    op.drop_table('social_automation_rules')
    op.drop_table('social_posts')
    op.drop_table('social_accounts')

