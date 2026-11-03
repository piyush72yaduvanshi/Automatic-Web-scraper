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

# Phase 2 Workflow Automation Engine
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowEvent,
)

# Phase 2 Deliverability & Mailbox Health
from app.models.deliverability import (
    EmailAccount,
    EmailDomain,
    EmailEvent,
)

# Phase 2 Advanced Campaigns & Sequences
from app.models.campaign import (
    CampaignMember,
    FollowupSequence,
    FollowupStep,
    CampaignEvent,
)

# Phase 2 Global Consent & Compliance
from app.models.compliance import (
    ConsentRecord,
    DataDeletionRequest,
)

# Phase 2 Social, SEO & Marketing
from app.models.marketing import (
    ContentItem,
    ContentCalendarEntry,
    SEOProject,
    SEOKeyword,
    PaidAdReport,
    CommunityDiscussion,
)

# Phase 2 Reporting
from app.models.reporting import (
    ReportSnapshot,
)

# Social Media Automation Models
from app.models.social import (
    SocialAccount,
    SocialPost,
    SocialAutomationRule,
    SocialPostMetric,
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
    # Phase 2
    "WorkflowDefinition",
    "WorkflowExecution",
    "WorkflowEvent",
    "EmailAccount",
    "EmailDomain",
    "EmailEvent",
    "CampaignMember",
    "FollowupSequence",
    "FollowupStep",
    "CampaignEvent",
    "ConsentRecord",
    "DataDeletionRequest",
    "ContentItem",
    "ContentCalendarEntry",
    "SEOProject",
    "SEOKeyword",
    "PaidAdReport",
    "CommunityDiscussion",
    "ReportSnapshot",
    "SocialAccount",
    "SocialPost",
    "SocialAutomationRule",
    "SocialPostMetric",
]
