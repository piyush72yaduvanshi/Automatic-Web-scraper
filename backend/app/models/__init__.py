"""Database models for AI Sales & CRM Operating System."""

from app.models.guid import GUID
from app.models.business_lead import BusinessLead
from app.models.lead_contact import LeadContact, ContactType
from app.models.lead_social_profile import LeadSocialProfile, SocialPlatform
from app.models.discovery_job import DiscoveryJob, JobStatus
from app.models.lead_source_evidence import LeadSourceEvidence

# CRM Models
from app.models.crm import (
    Company,
    Contact,
    Pipeline,
    PipelineStage,
    Deal,
    Activity,
    CRMTask,
    Meeting,
)

# Outreach & Messaging Models
from app.models.outreach import (
    OutreachCampaign,
    CampaignStep,
    OutreachApproval,
    Conversation,
    ConversationMessage,
    SuppressionRecord,
)

# AI Orchestration, Knowledge & Audit
from app.models.orchestration import (
    AgentRun,
    KnowledgeDocument,
    KnowledgeChunk,
    MemoryRecord,
    AuditLog,
)

__all__ = [
    "GUID",
    "BusinessLead",
    "LeadContact",
    "ContactType",
    "LeadSocialProfile",
    "SocialPlatform",
    "DiscoveryJob",
    "JobStatus",
    "LeadSourceEvidence",
    "Company",
    "Contact",
    "Pipeline",
    "PipelineStage",
    "Deal",
    "Activity",
    "CRMTask",
    "Meeting",
    "OutreachCampaign",
    "CampaignStep",
    "OutreachApproval",
    "Conversation",
    "ConversationMessage",
    "SuppressionRecord",
    "AgentRun",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "MemoryRecord",
    "AuditLog",
]
