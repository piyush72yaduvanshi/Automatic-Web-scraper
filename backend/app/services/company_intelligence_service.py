"""Company Intelligence Engine.

Researches companies and businesses to synthesize business opportunities, tech stack,
hiring signals, pain points, and recommended approach, strictly distinguishing:
- Verified Facts
- Inferred Insights
- Unknowns
"""

from typing import Dict, Any, List, Optional
import json
import logging
import uuid
from sqlalchemy.orm import Session

from app.models.business_lead import BusinessLead
from app.models.crm import Company
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class CompanyIntelligenceService:
    """Performs deep business research and structured opportunity analysis."""

    @classmethod
    async def analyze_company(
        cls,
        lead_id: Optional[str] = None,
        company_name: Optional[str] = None,
        website: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        raw_text: Optional[str] = None,
        search_snippets: Optional[List[str]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Produce a comprehensive company research report.
        Never hallucinate: clearly distinguishes verified facts from inferred insights and unknowns.
        """
        # Resolve from DB if lead_id is provided
        verified_contacts = []
        evidence_sources = []
        if lead_id and db:
            parsed_id = uuid.UUID(str(lead_id)) if isinstance(lead_id, str) else lead_id
            lead = db.query(BusinessLead).filter(BusinessLead.id == parsed_id).first()
            if lead:
                company_name = company_name or lead.business_name
                website = website or lead.website
                category = category or lead.category
                location = location or f"{lead.city or ''}, {lead.country or ''}".strip(", ")
                for c in lead.contacts:
                    verified_contacts.append(f"{c.contact_type.value}: {c.normalized_value or c.original_value}")
                for e in lead.source_evidence:
                    evidence_sources.append(f"{e.field_name}: {e.extracted_value} ({e.source_url})")

        name = company_name or "Target Business"
        snippets = "\n".join(search_snippets or [])[:3000]
        context_text = (raw_text or "")[:4000]

        prompt = f"""Analyze this company and generate a comprehensive B2B sales intelligence dossier.
Company Name: {name}
Website: {website or 'Not specified'}
Category / Industry: {category or 'General Commercial'}
Location: {location or 'Not specified'}
Existing Known Contacts: {', '.join(verified_contacts) if verified_contacts else 'None scraped'}
Scraped Content / Context:
{context_text}
Search Radar Snippets:
{snippets}

Requirements:
1. Executive Overview & Industry Classification
2. Probable Products and Services
3. Tech Stack Signals (e.g. WordPress, Shopify, React, Cloudflare, AWS, etc.)
4. Business Model (B2B, B2C, Agency, Healthcare, SaaS, Retail, etc.)
5. Hiring & Growth Signals (if detectable from snippets/text)
6. Critical Pain Points that software, CRM, or development services could solve
7. Suggested Service Offering & Recommended Outreach Angle
8. STRICT SEPARATION OF TRUTH:
   - 'verified_facts': items directly evidenced in the provided text
   - 'inferred_insights': reasonable AI inferences (marked clearly as unverified)
   - 'unknowns': missing pieces of information that require direct discovery
"""

        schema = """{
  "company_overview": "string",
  "industry": "string",
  "business_model": "string",
  "detected_tech_stack": ["string"],
  "hiring_signals": ["string"],
  "pain_points": ["string"],
  "suggested_offering": "string",
  "recommended_approach": "string",
  "verified_facts": ["string"],
  "inferred_insights": ["string"],
  "unknowns": ["string"],
  "confidence_score": 75
}"""

        result = await ai_router.generate_structured(
            prompt=prompt,
            schema_description=schema,
            system_instruction="You are an expert enterprise B2B sales intelligence researcher. Never invent fake phone numbers or addresses as verified facts.",
        )

        # Baseline safeguards if AI response is missing key keys
        if not result.get("verified_facts"):
            facts = [f"Company Name: {name}"]
            if website:
                facts.append(f"Official Website: {website}")
            if category:
                facts.append(f"Category: {category}")
            if verified_contacts:
                facts.extend([f"Identified Contact: {c}" for c in verified_contacts[:3]])
            result["verified_facts"] = facts

        if not result.get("unknowns"):
            result["unknowns"] = [
                "Budget and procurement timeline",
                "Internal decision maker contact preferences",
                "Current existing vendor contracts"
            ]

        if not result.get("inferred_insights"):
            result["inferred_insights"] = [
                f"Appears to operate in the {category or 'commercial'} sector",
                "May benefit from modern sales automation and digital workflow optimization"
            ]

        # If lead exists in DB, persist research
        if lead_id and db:
            parsed_id = uuid.UUID(str(lead_id)) if isinstance(lead_id, str) else lead_id
            lead = db.query(BusinessLead).filter(BusinessLead.id == parsed_id).first()
            if lead:
                lead.company_research = json.dumps(result)
                db.commit()

        return result
