"""Apply migration 009 directly to database"""
import sys
sys.path.insert(0, '.')

from app.core.database import engine
from sqlalchemy import text

def apply_migration():
    print("Applying migration 009_automation_tables...")
    
    with engine.connect() as conn:
        # Create automation_settings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS automation_settings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                setting_key VARCHAR(100) NOT NULL UNIQUE,
                setting_value TEXT NOT NULL,
                data_type VARCHAR(20) DEFAULT 'boolean',
                description TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_automation_settings_key ON automation_settings(setting_key)"))
        print("✓ Created automation_settings table")
        
        # Create lead_exceptions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lead_exceptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID,
                exception_type VARCHAR(100) NOT NULL,
                reason TEXT NOT NULL,
                severity VARCHAR(20) DEFAULT 'warning',
                resolved BOOLEAN DEFAULT FALSE,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                resolved_at TIMESTAMP
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lead_exceptions_lead_id ON lead_exceptions(lead_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lead_exceptions_type ON lead_exceptions(exception_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lead_exceptions_severity ON lead_exceptions(severity)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lead_exceptions_resolved ON lead_exceptions(resolved)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_exception_lead_type ON lead_exceptions(lead_id, exception_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_exception_severity_resolved ON lead_exceptions(severity, resolved)"))
        print("✓ Created lead_exceptions table")
        
        # Add columns to business_leads
        try:
            conn.execute(text("ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS outreach_enrolled BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS outreach_enrollment_date TIMESTAMP"))
            conn.execute(text("ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS crm_converted BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS crm_conversion_date TIMESTAMP"))
            conn.execute(text("ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS email_enrichment_status VARCHAR(50) DEFAULT 'pending'"))
            conn.execute(text("ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS last_automation_run TIMESTAMP"))
            print("✓ Added columns to business_leads")
        except Exception as e:
            print(f"  Note: Columns may already exist: {e}")
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_outreach_enrolled ON business_leads(outreach_enrolled)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_crm_converted ON business_leads(crm_converted)"))
        print("✓ Created indexes")
        
        # Seed settings
        conn.execute(text("""
            INSERT INTO automation_settings (setting_key, setting_value, data_type, description)
            VALUES
                ('auto_enroll_to_outreach', 'true', 'boolean', 'Automatically enroll qualified leads in outreach sequences'),
                ('auto_approve_emails', 'true', 'boolean', 'Automatically approve AI-generated outreach emails'),
                ('auto_convert_to_crm', 'true', 'boolean', 'Automatically convert qualified leads to CRM companies/contacts/deals'),
                ('min_score_for_outreach', '70', 'integer', 'Minimum qualification score required for automatic outreach enrollment'),
                ('min_score_for_crm', '60', 'integer', 'Minimum qualification score required for automatic CRM conversion'),
                ('email_enrichment_enabled', 'true', 'boolean', 'Enable automatic email enrichment for leads without email'),
                ('bulk_processing_batch_size', '50', 'integer', 'Number of leads to process in each batch')
            ON CONFLICT (setting_key) DO NOTHING
        """))
        print("✓ Seeded automation settings")
        
        # Update alembic version
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('009_automation_tables') ON CONFLICT DO NOTHING"))
        print("✓ Updated alembic_version")
        
        conn.commit()
        print("\n✅ Migration 009 applied successfully!")

if __name__ == '__main__':
    apply_migration()
