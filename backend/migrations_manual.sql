-- Manual migration for call_logs, notes, emails tables
-- Migration 008: CRM Call Logs, Notes, Emails

-- 1. Create call_logs table
CREATE TABLE IF NOT EXISTS call_logs (
    id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    deal_id UUID REFERENCES deals(id) ON DELETE SET NULL,
    direction VARCHAR(20) NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    phone_number VARCHAR(100),
    recording_url VARCHAR(500),
    transcript TEXT,
    outcome VARCHAR(50),
    notes TEXT,
    call_started_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_call_logs_contact_id ON call_logs(contact_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_company_id ON call_logs(company_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_deal_id ON call_logs(deal_id);
CREATE INDEX IF NOT EXISTS idx_call_logs_direction ON call_logs(direction);
CREATE INDEX IF NOT EXISTS idx_call_logs_phone_number ON call_logs(phone_number);
CREATE INDEX IF NOT EXISTS idx_call_logs_created_at ON call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_call_logs_call_started_at ON call_logs(call_started_at);

-- 2. Create notes table
CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    lead_id UUID,
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    created_by VARCHAR(100),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_contact_id ON notes(contact_id);
CREATE INDEX IF NOT EXISTS idx_notes_company_id ON notes(company_id);
CREATE INDEX IF NOT EXISTS idx_notes_deal_id ON notes(deal_id);
CREATE INDEX IF NOT EXISTS idx_notes_lead_id ON notes(lead_id);
CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at);
CREATE INDEX IF NOT EXISTS idx_notes_is_pinned ON notes(is_pinned);

-- 3. Create emails table
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    deal_id UUID REFERENCES deals(id) ON DELETE SET NULL,
    subject VARCHAR(500),
    body_text TEXT,
    body_html TEXT,
    direction VARCHAR(20) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    sent_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_emails_contact_id ON emails(contact_id);
CREATE INDEX IF NOT EXISTS idx_emails_company_id ON emails(company_id);
CREATE INDEX IF NOT EXISTS idx_emails_deal_id ON emails(deal_id);
CREATE INDEX IF NOT EXISTS idx_emails_direction ON emails(direction);
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);
CREATE INDEX IF NOT EXISTS idx_emails_sent_at ON emails(sent_at);
CREATE INDEX IF NOT EXISTS idx_emails_created_at ON emails(created_at);

-- 4. Enhance pipeline_stages table
ALTER TABLE pipeline_stages ADD COLUMN IF NOT EXISTS is_closed_won BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE pipeline_stages ADD COLUMN IF NOT EXISTS is_closed_lost BOOLEAN NOT NULL DEFAULT false;

-- 5. Enhance crm_tasks table
ALTER TABLE crm_tasks ADD COLUMN IF NOT EXISTS contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL;
ALTER TABLE crm_tasks ADD COLUMN IF NOT EXISTS deal_id UUID REFERENCES deals(id) ON DELETE SET NULL;
ALTER TABLE crm_tasks ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_crm_tasks_contact_id ON crm_tasks(contact_id);
CREATE INDEX IF NOT EXISTS idx_crm_tasks_deal_id ON crm_tasks(deal_id);

-- Update alembic_version
INSERT INTO alembic_version (version_num) VALUES ('008')
ON CONFLICT (version_num) DO NOTHING;
