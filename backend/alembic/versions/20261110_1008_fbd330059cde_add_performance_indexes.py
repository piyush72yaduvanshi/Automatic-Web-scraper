"""add_performance_indexes

Revision ID: fbd330059cde
Revises: 004
Create Date: 2026-11-10 10:08:11.295000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbd330059cde'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Business Leads - Most queried table
    op.create_index('idx_business_leads_status', 'business_leads', ['status'], if_not_exists=True)
    op.create_index('idx_business_leads_source_provider', 'business_leads', ['source_provider'], if_not_exists=True)
    op.create_index('idx_business_leads_qualification_score', 'business_leads', ['qualification_score'], if_not_exists=True)
    op.create_index('idx_business_leads_created_at', 'business_leads', ['created_at'], postgresql_using='btree', if_not_exists=True)
    
    # CRM Core
    op.create_index('idx_companies_status', 'companies', ['status'], if_not_exists=True)
    op.create_index('idx_deals_status', 'deals', ['status'], if_not_exists=True)
    op.create_index('idx_deals_stage_id', 'deals', ['stage_id'], if_not_exists=True)
    op.create_index('idx_contacts_company_id', 'contacts', ['company_id'], if_not_exists=True)
    op.create_index('idx_activities_company_id', 'activities', ['company_id'], if_not_exists=True)
    
    # Discovery System
    op.create_index('idx_discovery_jobs_status', 'discovery_jobs', ['status'], if_not_exists=True)
    op.create_index('idx_discovery_jobs_created_at', 'discovery_jobs', ['created_at'], postgresql_using='btree', if_not_exists=True)
    
    # Outreach
    op.create_index('idx_outreach_approvals_status', 'outreach_approvals', ['status'], if_not_exists=True)
    op.create_index('idx_conversations_status', 'conversations', ['status'], if_not_exists=True)
    op.create_index('idx_conversations_last_message_at', 'conversations', ['last_message_at'], postgresql_using='btree', if_not_exists=True)
    
    # pgvector Semantic Search - CRITICAL for RAG performance
    # Only create if pgvector extension is enabled
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
                CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding 
                ON knowledge_chunks 
                USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_index('idx_business_leads_status', if_exists=True)
    op.drop_index('idx_business_leads_source_provider', if_exists=True)
    op.drop_index('idx_business_leads_qualification_score', if_exists=True)
    op.drop_index('idx_business_leads_created_at', if_exists=True)
    op.drop_index('idx_companies_status', if_exists=True)
    op.drop_index('idx_deals_status', if_exists=True)
    op.drop_index('idx_deals_stage_id', if_exists=True)
    op.drop_index('idx_contacts_company_id', if_exists=True)
    op.drop_index('idx_activities_company_id', if_exists=True)
    op.drop_index('idx_discovery_jobs_status', if_exists=True)
    op.drop_index('idx_discovery_jobs_created_at', if_exists=True)
    op.drop_index('idx_outreach_approvals_status', if_exists=True)
    op.drop_index('idx_conversations_status', if_exists=True)
    op.drop_index('idx_conversations_last_message_at', if_exists=True)
    op.execute("DROP INDEX IF EXISTS idx_knowledge_chunks_embedding;")
