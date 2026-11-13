-- Apply migration 009 manually
-- Add automation_settings and lead_exceptions tables

-- Create automation_settings table
CREATE TABLE IF NOT EXISTS automation_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    data_type VARCHAR(20) DEFAULT 'boolean',
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_automation_settings_key ON automation_settings(setting_key);

-- Create lead_exceptions table
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
);

CREATE INDEX IF NOT EXISTS idx_lead_exceptions_lead_id ON lead_exceptions(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_exceptions_type ON lead_exceptions(exception_type);
CREATE INDEX IF NOT EXISTS idx_lead_exceptions_severity ON lead_exceptions(severity);
CREATE INDEX IF NOT EXISTS idx_lead_exceptions_resolved ON lead_exceptions(resolved);
CREATE INDEX IF NOT EXISTS idx_lead_exceptions_created_at ON lead_exceptions(created_at);
CREATE INDEX IF NOT EXISTS idx_exception_lead_type ON lead_exceptions(lead_id, exception_type);
CREATE INDEX IF NOT EXISTS idx_exception_severity_resolved ON lead_exceptions(severity, resolved);

-- Add automation tracking columns to business_leads
ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS outreach_enrolled BOOLEAN DEFAULT FALSE;
ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS outreach_enrollment_date TIMESTAMP;
ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS crm_converted BOOLEAN DEFAULT FALSE;
ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS crm_conversion_date TIMESTAMP;
ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS email_enrichment_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE business_leads ADD COLUMN IF NOT EXISTS last_automation_run TIMESTAMP;

-- Create indexes on new columns
CREATE INDEX IF NOT EXISTS idx_outreach_enrolled ON business_leads(outreach_enrolled);
CREATE INDEX IF NOT EXISTS idx_crm_converted ON business_leads(crm_converted);

-- Seed default automation settings
INSERT INTO automation_settings (id, setting_key, setting_value, data_type, description)
VALUES
    (gen_random_uuid(), 'auto_enroll_to_outreach', 'true', 'boolean', 'Automatically enroll qualified leads in outreach sequences'),
    (gen_random_uuid(), 'auto_approve_emails', 'true', 'boolean', 'Automatically approve AI-generated outreach emails'),
    (gen_random_uuid(), 'auto_convert_to_crm', 'true', 'boolean', 'Automatically convert qualified leads to CRM companies/contacts/deals'),
    (gen_random_uuid(), 'min_score_for_outreach', '70', 'integer', 'Minimum qualification score required for automatic outreach enrollment'),
    (gen_random_uuid(), 'min_score_for_crm', '60', 'integer', 'Minimum qualification score required for automatic CRM conversion'),
    (gen_random_uuid(), 'email_enrichment_enabled', 'true', 'boolean', 'Enable automatic email enrichment for leads without email'),
    (gen_random_uuid(), 'bulk_processing_batch_size', '50', 'integer', 'Number of leads to process in each batch')
ON CONFLICT (setting_key) DO NOTHING;

-- Update alembic_version
INSERT INTO alembic_version (version_num) VALUES ('009_automation_tables')
ON CONFLICT (version_num) DO NOTHING;
