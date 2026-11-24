"""Add discovery automation schema

Revision ID: 006
Revises: 20261110_1008_fbd330059cde
Create Date: 2026-11-10 20:50:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006'
down_revision: Union[str, None] = 'fbd330059cde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create discovery automation tables."""
    
    # 1. Create discovery_schedules table
    op.create_table(
        'discovery_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('schedule_type', sa.String(50), server_default='DAILY', nullable=False),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('interval_hours', sa.Integer(), nullable=True),
        sa.Column('max_leads_per_run', sa.Integer(), server_default='50', nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_discovery_schedule_name', 'discovery_schedules', ['name'])
    op.create_index('idx_discovery_schedule_active', 'discovery_schedules', ['is_active'])
    op.create_index('idx_discovery_schedule_last_run', 'discovery_schedules', ['last_run_at'])
    op.create_index('idx_discovery_schedule_next_run', 'discovery_schedules', ['next_run_at'])

    # 2. Create discovery_targets table
    op.create_table(
        'discovery_targets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discovery_schedules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_value', sa.String(255), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('idx_discovery_target_schedule', 'discovery_targets', ['schedule_id'])
    op.create_index('idx_discovery_target_type', 'discovery_targets', ['target_type'])

    # 3. Create discovery_runs table
    op.create_table(
        'discovery_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('discovery_schedules.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), server_default='RUNNING', nullable=False),
        sa.Column('leads_discovered', sa.Integer(), server_default='0', nullable=False),
        sa.Column('target_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_discovery_run_schedule', 'discovery_runs', ['schedule_id'])
    op.create_index('idx_discovery_run_status', 'discovery_runs', ['status'])
    op.create_index('idx_discovery_run_started', 'discovery_runs', ['started_at'])


def downgrade() -> None:
    """Drop discovery automation tables."""
    
    op.drop_index('idx_discovery_run_started', table_name='discovery_runs')
    op.drop_index('idx_discovery_run_status', table_name='discovery_runs')
    op.drop_index('idx_discovery_run_schedule', table_name='discovery_runs')
    op.drop_table('discovery_runs')
    
    op.drop_index('idx_discovery_target_type', table_name='discovery_targets')
    op.drop_index('idx_discovery_target_schedule', table_name='discovery_targets')
    op.drop_table('discovery_targets')
    
    op.drop_index('idx_discovery_schedule_next_run', table_name='discovery_schedules')
    op.drop_index('idx_discovery_schedule_last_run', table_name='discovery_schedules')
    op.drop_index('idx_discovery_schedule_active', table_name='discovery_schedules')
    op.drop_index('idx_discovery_schedule_name', table_name='discovery_schedules')
    op.drop_table('discovery_schedules')
