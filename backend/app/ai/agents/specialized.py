"""The 15 Specialized AI Sales & CRM Agents.

Each agent has a defined role, input/output schema, scoped tools, execution boundaries,
and automated fallback behavior.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from sqlalchemy.orm import Session

from app.ai.agents.base import BaseSpecializedAgent
from app.ai.tools.registry import ToolRegistry
from app.providers.ai.router import ai_router
from app.models.business_lead import BusinessLead
from app.models.crm import Company, Deal, Contact, CRMTask
from app.models.orchestration import KnowledgeDocument

logger = logging.getLogger(__name__)


# -------------------------------------------------------------
# 1. Lead Discovery Agent
# -------------------------------------------------------------
class LeadDiscoveryAgent(BaseSpecializedAgent):
    name = "lead_discovery_agent"
    role = "Lead Discovery Specialist"
    description = "Formulates optimal search queries, categories, and geographic coordinates for business discovery."
    allowed_tools = ["search_leads_db"]

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        query = input_data.get("query", "software development")
        location = input_data.get("location", "Bangalore")
        target_icp = input_data.get("target_icp", "")

        prompt = f"""You are an expert Lead Discovery Agent.
Formulate search recommendations and optimal queries to discover target businesses.
User Request: Find businesses matching '{query}' in '{location}'.
Target ICP: {target_icp}

Generate:
1. 'recommended_queries': List of 3-5 high-intent Google Maps / Search queries
2. 'target_categories': Specific commercial business categories
3. 'search_radius_km': Recommended search radius
4. 'discovery_strategy': Brief explanation of discovery tactic
"""
        schema = """{
  "recommended_queries": ["string"],
  "target_categories": ["string"],
  "search_radius_km": 15,
  "discovery_strategy": "string"
}"""
        res = await ai_router.generate_structured(prompt, schema)
        return res


# -------------------------------------------------------------
# 2. Company Research Agent
# -------------------------------------------------------------
class CompanyResearchAgent(BaseSpecializedAgent):
    name = "company_research_agent"
    role = "Company Intelligence Analyst"
    description = "Conducts deep business research, analyzing products, tech stack, and pain points."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        from app.services.company_intelligence_service import CompanyIntelligenceService
        return await CompanyIntelligenceService.analyze_company(
            lead_id=input_data.get("lead_id"),
            company_name=input_data.get("company_name"),
            website=input_data.get("website"),
            category=input_data.get("category"),
            location=input_data.get("location"),
            raw_text=input_data.get("raw_text"),
            db=db,
        )


# -------------------------------------------------------------
# 3. Contact Enrichment Agent
# -------------------------------------------------------------
class ContactEnrichmentAgent(BaseSpecializedAgent):
    name = "contact_enrichment_agent"
    role = "Contact Enrichment Specialist"
    description = "Identifies key decision makers, categorizes contact channels, and verifies reachability."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        raw_text = input_data.get("text", "")
        company_name = input_data.get("company_name", "Target Business")

        prompt = f"""Analyze the following digital footprint for {company_name} and extract key decision makers:
{raw_text[:3000]}

Identify:
1. Executive names and suspected titles (CEO, Founder, Director, VP)
2. Professional email patterns and public contact addresses
3. Recommended outreach contact priority
"""
        schema = """{
  "key_people": [{"name": "string", "title": "string", "relevance": "High"}],
  "contact_channels": [{"channel": "EMAIL", "value": "string", "confidence": "High"}],
  "reachability_rating": "High",
  "enrichment_summary": "string"
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 4. Lead Qualification Agent
# -------------------------------------------------------------
class LeadQualificationAgent(BaseSpecializedAgent):
    name = "lead_qualification_agent"
    role = "Lead Qualification Specialist"
    description = "Evaluates leads using configurable ICP factors and generates 0-100 score."
    allowed_tools = ["calculate_icp_score"]

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        lead_id = input_data.get("lead_id")
        if not lead_id:
            raise ValueError("lead_id is required for lead qualification")
        from app.services.lead_qualification_service import LeadQualificationService
        return await LeadQualificationService.qualify_lead(
            lead_id=lead_id,
            db=db,
            icp_profile=input_data.get("icp_profile"),
            custom_weights=input_data.get("weights"),
        )


# -------------------------------------------------------------
# 5. ICP Analysis Agent
# -------------------------------------------------------------
class ICPAnalysisAgent(BaseSpecializedAgent):
    name = "icp_analysis_agent"
    role = "ICP Strategist"
    description = "Defines and optimizes Ideal Customer Profile criteria and qualification rubrics."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        my_service = input_data.get("service_offering", "Full-stack software engineering and CRM systems")
        target_market = input_data.get("target_market", "B2B Mid-market & funded startups")

        prompt = f"""You are an ICP Strategist.
Define an actionable Ideal Customer Profile definition for:
Service: {my_service}
Target Market: {target_market}

Specify:
1. Target industries and company sizes
2. Essential qualifying triggers (signals that mean they need this now)
3. Hard disqualifiers (signals to reject immediately)
4. Key decision maker personas to target
"""
        schema = """{
  "icp_summary": "string",
  "target_industries": ["string"],
  "company_size_sweet_spot": "string",
  "qualifying_triggers": ["string"],
  "disqualifiers": ["string"],
  "target_personas": ["string"]
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 6. Competitor Research Agent
# -------------------------------------------------------------
class CompetitorResearchAgent(BaseSpecializedAgent):
    name = "competitor_research_agent"
    role = "Market & Competitor Analyst"
    description = "Analyzes competitor landscape and generates battlecards and differentiation angles."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        domain = input_data.get("industry_or_category", "CRM and Sales Automation")
        prompt = f"""Analyze the competitive landscape for: {domain}.
Identify:
1. Common competitor limitations and pain points
2. Key differentiation angles and value propositions
3. Suggested objection responses when a prospect says 'we already use a competitor'
"""
        schema = """{
  "market_category": "string",
  "common_competitor_gaps": ["string"],
  "our_key_differentiators": ["string"],
  "objection_battlecard": [{"competitor_type": "string", "our_counter_angle": "string"}]
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 7. Outreach Strategy Agent
# -------------------------------------------------------------
class OutreachStrategyAgent(BaseSpecializedAgent):
    name = "outreach_strategy_agent"
    role = "Outreach Strategist"
    description = "Designs multi-touch sales sequences and cadence schedules across Email and WhatsApp."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        target_audience = input_data.get("audience", "Founders of local dental clinics or tech agencies")
        channel = input_data.get("channel", "EMAIL")

        prompt = f"""Design a high-converting, compliant B2B cold outreach campaign sequence.
Audience: {target_audience}
Primary Channel: {channel}

Define a 3-step sequence:
- Step 1: Initial personalized introductory note
- Step 2: Gentle follow-up with concrete value asset (e.g. audit or case study)
- Step 3: Polite breakup note
Include delay days between steps and subject line ideas.
"""
        schema = """{
  "campaign_theme": "string",
  "recommended_cadence": "string",
  "steps": [
    {"step_number": 1, "delay_days": 0, "subject_line": "string", "intent": "string"},
    {"step_number": 2, "delay_days": 3, "subject_line": "string", "intent": "string"},
    {"step_number": 3, "delay_days": 5, "subject_line": "string", "intent": "string"}
  ]
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 8. Email Personalization Agent
# -------------------------------------------------------------
class EmailPersonalizationAgent(BaseSpecializedAgent):
    name = "email_personalization_agent"
    role = "Outreach Personalization Specialist"
    description = "Drafts bespoke cold outreach emails weaving in verified company facts and pain points."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        company_name = input_data.get("company_name", "Prospective Business")
        contact_name = input_data.get("contact_name", "Team")
        pain_points = input_data.get("pain_points", ["Manual customer intake"])
        offering = input_data.get("offering", "AI Sales & CRM Automation")
        verified_facts = input_data.get("verified_facts", [])

        prompt = f"""Draft a tailored, non-spammy cold outreach email.
Recipient Name: {contact_name}
Company Name: {company_name}
Specific Pain Points: {', '.join(pain_points) if isinstance(pain_points, list) else pain_points}
Our Offering: {offering}
Verified Evidence to reference: {', '.join(verified_facts) if isinstance(verified_facts, list) else verified_facts}

Rules:
- Under 120 words
- No pushy sales jargon
- One clear, low-friction call-to-action (e.g. 10-minute chat)
- Professional and authentic
"""
        schema = """{
  "subject_line": "string",
  "email_body": "string",
  "personalization_reason": "string",
  "call_to_action": "string"
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 9. Follow-up Planning Agent
# -------------------------------------------------------------
class FollowupPlanningAgent(BaseSpecializedAgent):
    name = "followup_planning_agent"
    role = "Follow-up Cadence Planner"
    description = "Generates contextual follow-up messages based on prior interaction history."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        company_name = input_data.get("company_name", "Client")
        previous_subject = input_data.get("previous_subject", "Quick question regarding software tools")
        days_since = input_data.get("days_since", 4)

        prompt = f"""Draft a polite, concise follow-up message.
Company: {company_name}
Previous Subject: {previous_subject}
Days Since Previous Email: {days_since}

Rules:
- Acknowledge their busy schedule
- Add one quick fresh perspective
- Keep it under 75 words
"""
        schema = """{
  "followup_subject": "string",
  "followup_body": "string",
  "suggested_send_timing": "string"
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 10. Reply Classification Agent
# -------------------------------------------------------------
class ReplyClassificationAgent(BaseSpecializedAgent):
    name = "reply_classification_agent"
    role = "Inbound Reply Classifier"
    description = "Classifies incoming prospect replies and drafts recommended next responses."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        reply_text = input_data.get("reply_text", "")
        company_name = input_data.get("company_name", "Client")

        prompt = f"""Classify this inbound prospect reply for {company_name}:
"{reply_text}"

Classify into exactly one category:
- INTERESTED (Wants demo/pricing/meeting)
- OBJECTION (Has concerns or questions)
- NOT_NOW (Too busy, check back in Q3/Q4)
- UNSUBSCRIBE (Requests removal from list)
- QUESTION (Asking for more technical details)
- OUT_OF_OFFICE (Automated auto-reply)

Provide:
1. 'classification': The category
2. 'sentiment': Positive, Neutral, or Negative
3. 'suggested_reply': Draft response (or empty if UNSUBSCRIBE/OOO)
4. 'requires_human_attention': True/False
"""
        schema = """{
  "classification": "INTERESTED",
  "sentiment": "Positive",
  "suggested_reply": "string",
  "requires_human_attention": true
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 11. CRM Management Agent
# -------------------------------------------------------------
class CRMManagementAgent(BaseSpecializedAgent):
    name = "crm_management_agent"
    role = "CRM Operations Manager"
    description = "Monitors deals, identifies stalled accounts, and recommends pipeline updates."
    allowed_tools = ["query_crm_pipeline"]

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        pipeline_data = ToolRegistry.execute_tool("query_crm_pipeline", db=db)
        prompt = f"""You are a CRM Operations Manager.
Analyze this CRM pipeline snapshot:
{json.dumps(pipeline_data)}

Recommend:
1. Stalled deals that need immediate follow-up tasks
2. Suggested pipeline hygiene improvements
3. Top 3 priority actions for today
"""
        schema = """{
  "pipeline_health_status": "Healthy",
  "recommended_actions": ["string"],
  "followup_recommendations": [{"deal_title": "string", "recommended_action": "string"}]
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 12. Meeting Preparation Agent
# -------------------------------------------------------------
class MeetingPreparationAgent(BaseSpecializedAgent):
    name = "meeting_preparation_agent"
    role = "Executive Meeting Prep Specialist"
    description = "Creates executive briefing dossiers for scheduled sales discovery and demo meetings."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        meeting_title = input_data.get("meeting_title", "Discovery Call")
        company_name = input_data.get("company_name", "Target Prospect")
        company_context = input_data.get("company_context", "")

        prompt = f"""Prepare an executive meeting dossier for:
Meeting: {meeting_title}
Company: {company_name}
Known Background: {company_context}

Generate:
1. Executive briefing & company background
2. Key discovery questions to ask
3. Anticipated objections and ready responses
4. Ideal next step to secure at the end of the call
"""
        schema = """{
  "executive_summary": "string",
  "key_discovery_questions": ["string"],
  "potential_objections": ["string"],
  "desired_call_outcome": "string"
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 13. Sales Analytics Agent
# -------------------------------------------------------------
class SalesAnalyticsAgent(BaseSpecializedAgent):
    name = "sales_analytics_agent"
    role = "Sales Performance Analyst"
    description = "Analyzes lead conversion rates, pipeline velocity, and campaign return on effort."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        total_leads = db.query(BusinessLead).count()
        qualified_leads = db.query(BusinessLead).filter(BusinessLead.status == "qualified").count()
        deals = db.query(Deal).all()
        won_deals = sum(1 for d in deals if d.status == "won")
        won_value = sum(d.amount for d in deals if d.status == "won")
        open_value = sum(d.amount for d in deals if d.status == "open")

        stats_summary = {
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "qualification_rate": f"{(qualified_leads/total_leads*100):.1f}%" if total_leads > 0 else "0%",
            "total_deals": len(deals),
            "won_deals": won_deals,
            "won_value": won_value,
            "open_pipeline_value": open_value,
        }

        prompt = f"""You are a Senior Sales Analyst. Review these CRM metrics:
{json.dumps(stats_summary)}

Provide:
1. Performance summary
2. Lead generation bottlenecks
3. 2 key recommendations to improve revenue velocity
"""
        schema = """{
  "performance_summary": "string",
  "identified_bottlenecks": ["string"],
  "strategic_recommendations": ["string"]
}"""
        ai_res = await ai_router.generate_structured(prompt, schema)
        return {"metrics": stats_summary, "analysis": ai_res}


# -------------------------------------------------------------
# 14. Knowledge Retrieval Agent
# -------------------------------------------------------------
class KnowledgeRetrievalAgent(BaseSpecializedAgent):
    name = "knowledge_retrieval_agent"
    role = "Knowledge Base & RAG Assistant"
    description = "Retrieves sales playbooks, service offerings, and case studies to answer questions."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        query = input_data.get("query", "our service offerings")
        docs = db.query(KnowledgeDocument).all()
        doc_texts = [f"Title: {d.title} (Category: {d.category})\nContent: {d.content}" for d in docs[:5]]
        docs_str = "\n---\n".join(doc_texts) if doc_texts else "No custom knowledge documents uploaded yet."

        prompt = f"""Answer the following question using ONLY our stored knowledge documents:
Question: {query}

Available Knowledge Documents:
{docs_str}

Provide:
1. 'answer': Direct, helpful answer
2. 'source_citations': List of cited document titles
3. 'confidence': High, Medium, or Low
"""
        schema = """{
  "answer": "string",
  "source_citations": ["string"],
  "confidence": "High"
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# 15. Workflow Planning Agent
# -------------------------------------------------------------
class WorkflowPlanningAgent(BaseSpecializedAgent):
    name = "workflow_planning_agent"
    role = "Master Autonomous Workflow Planner"
    description = "Decomposes complex sales objectives into structured, multi-agent execution steps."

    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        user_request = input_data.get("request", "Find leads and qualify them for outreach")

        prompt = f"""You are the Master Workflow Planning Agent.
Decompose this sales objective into an actionable execution workflow:
Objective: "{user_request}"

Break down into sequential steps, assigning each step to one of our specialized agents:
- lead_discovery_agent
- company_research_agent
- contact_enrichment_agent
- lead_qualification_agent
- outreach_strategy_agent
- email_personalization_agent
- crm_management_agent
"""
        schema = """{
  "workflow_name": "string",
  "total_steps": 4,
  "steps": [
    {"step_number": 1, "agent": "string", "action_description": "string", "requires_human_approval": false}
  ],
  "estimated_duration_seconds": 60
}"""
        return await ai_router.generate_structured(prompt, schema)


# -------------------------------------------------------------
# Central Agent Registry
# -------------------------------------------------------------
class AgentRegistry:
    """Registry managing all 15 specialized agents."""

    _agents: Dict[str, BaseSpecializedAgent] = {
        LeadDiscoveryAgent.name: LeadDiscoveryAgent(),
        CompanyResearchAgent.name: CompanyResearchAgent(),
        ContactEnrichmentAgent.name: ContactEnrichmentAgent(),
        LeadQualificationAgent.name: LeadQualificationAgent(),
        ICPAnalysisAgent.name: ICPAnalysisAgent(),
        CompetitorResearchAgent.name: CompetitorResearchAgent(),
        OutreachStrategyAgent.name: OutreachStrategyAgent(),
        EmailPersonalizationAgent.name: EmailPersonalizationAgent(),
        FollowupPlanningAgent.name: FollowupPlanningAgent(),
        ReplyClassificationAgent.name: ReplyClassificationAgent(),
        CRMManagementAgent.name: CRMManagementAgent(),
        MeetingPreparationAgent.name: MeetingPreparationAgent(),
        SalesAnalyticsAgent.name: SalesAnalyticsAgent(),
        KnowledgeRetrievalAgent.name: KnowledgeRetrievalAgent(),
        WorkflowPlanningAgent.name: WorkflowPlanningAgent(),
    }

    @classmethod
    def get_agent(cls, name: str) -> Optional[BaseSpecializedAgent]:
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": a.name,
                "role": a.role,
                "description": a.description,
                "allowed_tools": a.allowed_tools,
                "max_execution_steps": a.max_execution_steps,
            }
            for a in cls._agents.values()
        ]
