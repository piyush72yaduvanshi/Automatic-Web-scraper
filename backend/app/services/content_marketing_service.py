"""Social Media & Content Marketing Engine.

Supports multi-channel content planning (LinkedIn, X, Instagram, Facebook, Reddit, Quora),
the 5 core content pillars, AI-driven platform repurposing, content calendar scheduling,
and strict human approval governance.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.marketing import ContentItem, ContentCalendarEntry
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class ContentMarketingService:
    """Manages content ideation, platform-specific drafting, calendar scheduling, and approval."""

    PILLARS = [
        "TECHNICAL_EXPERTISE",
        "PROOF_OF_WORK",
        "PROBLEM_AWARENESS",
        "COMPANY_UPDATES",
        "OFFERS_AND_SERVICES",
    ]

    PLATFORMS = ["LINKEDIN", "X", "INSTAGRAM", "FACEBOOK", "REDDIT", "QUORA"]

    @classmethod
    def list_content_items(cls, db: Session, pillar: Optional[str] = None) -> List[Dict[str, Any]]:
        """List content drafts and approved items."""
        cls.seed_default_content_if_empty(db)
        q = db.query(ContentItem)
        if pillar:
            q = q.filter(ContentItem.pillar == pillar)
        items = q.order_by(ContentItem.created_at.desc()).all()
        return [
            {
                "id": str(i.id),
                "title": i.title,
                "pillar": i.pillar,
                "target_audience": i.target_audience,
                "platforms": json.loads(i.platforms_json) if i.platforms_json else [],
                "core_idea": i.core_idea,
                "platform_drafts": json.loads(i.platform_drafts_json) if i.platform_drafts_json else {},
                "status": i.status,
                "published_at": i.published_at.isoformat() if i.published_at else None,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]

    @classmethod
    async def create_and_repurpose_content(cls, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Takes a core idea and pillar, then prompts AI to formulate
        native drafts tailored to each selected platform (LinkedIn, X, Reddit).
        """
        title = data.get("title", "Untitled Content")
        pillar = data.get("pillar", "TECHNICAL_EXPERTISE").upper()
        if pillar not in cls.PILLARS:
            pillar = "TECHNICAL_EXPERTISE"

        platforms = data.get("platforms", ["LINKEDIN", "X"])
        core_idea = data.get("core_idea", "")
        target_audience = data.get("target_audience", "B2B Founders & Sales Leaders")

        prompt = f"""You are a Multi-Platform Social Media & Content Strategist.
Create tailored native drafts for the following platforms based on this core insight:
Pillar: {pillar}
Target Audience: {target_audience}
Core Idea: \"{core_idea}\"
Platforms: {', '.join(platforms)}

Formatting Guidelines:
- LINKEDIN: Strong 2-line hook, line breaks, tactical breakdown, 3 bullet takeaways, low-friction question at end. No hashtags.
- X: Punchy tweet or 3-part micro-thread under 280 characters per tweet. High insight-to-word ratio.
- REDDIT: Authentic, non-promotional discussion prompt for relevant professional subreddits. Focus on shared challenges and lessons learned.

Provide structured JSON with draft copy for each requested platform.
"""
        schema = """{
  "platform_drafts": {
    "LINKEDIN": "string",
    "X": "string",
    "REDDIT": "string"
  },
  "summary_hook": "string"
}"""
        try:
            ai_res = await ai_router.generate_structured(prompt, schema)
            drafts = ai_res.get("platform_drafts", {})
        except Exception as e:
            logger.warning(f"AI content drafting failed, using template fallback: {e}")
            drafts = {}

        if not drafts or not isinstance(drafts, dict) or len(drafts) == 0:
            drafts = {
                p: f"[{p} Insight]: {core_idea}\n\nKey Takeaway for {target_audience}."
                for p in platforms
            }

        item = ContentItem(
            title=title,
            pillar=pillar,
            target_audience=target_audience,
            platforms_json=json.dumps(platforms),
            core_idea=core_idea,
            platform_drafts_json=json.dumps(drafts),
            status="PENDING_APPROVAL",
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        return {
            "id": str(item.id),
            "title": item.title,
            "pillar": item.pillar,
            "status": item.status,
            "platform_drafts": drafts,
        }

    @classmethod
    def schedule_calendar_entry(cls, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Schedules an approved content item onto the publishing calendar."""
        item_id = uuid.UUID(str(data.get("content_item_id")))
        item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
        if not item:
            raise ValueError(f"ContentItem '{item_id}' not found")

        scheduled_time = datetime.fromisoformat(data.get("scheduled_for")) if isinstance(data.get("scheduled_for"), str) else data.get("scheduled_for", datetime.utcnow())

        entry = ContentCalendarEntry(
            content_item_id=item.id,
            channel=data.get("channel", "LINKEDIN").upper(),
            scheduled_for=scheduled_time,
            status="SCHEDULED",
            publishing_provider_status="NOT_CONFIGURED",  # Honest status: automated posting API unconfigured
        )
        item.status = "SCHEDULED"
        db.add(entry)
        db.commit()
        db.refresh(entry)

        return {
            "calendar_entry_id": str(entry.id),
            "channel": entry.channel,
            "scheduled_for": entry.scheduled_for.isoformat(),
            "status": entry.status,
            "publishing_provider_status": entry.publishing_provider_status,
        }

    @classmethod
    def list_calendar_entries(cls, db: Session) -> List[Dict[str, Any]]:
        """List upcoming scheduled calendar entries."""
        entries = db.query(ContentCalendarEntry).order_by(ContentCalendarEntry.scheduled_for.asc()).all()
        return [
            {
                "id": str(e.id),
                "content_item_id": str(e.content_item_id),
                "content_title": e.content_item.title if e.content_item else "Untitled",
                "pillar": e.content_item.pillar if e.content_item else "General",
                "channel": e.channel,
                "scheduled_for": e.scheduled_for.isoformat() if e.scheduled_for else None,
                "status": e.status,
                "publishing_provider_status": e.publishing_provider_status,
            }
            for e in entries
        ]

    @classmethod
    def seed_default_content_if_empty(cls, db: Session) -> None:
        """Seed sample content items mapped across pillars."""
        if db.query(ContentItem).count() > 0:
            return

        samples = [
            {
                "title": "Why Most B2B Cold Outreach Fails to Convert",
                "pillar": "PROBLEM_AWARENESS",
                "target_audience": "B2B Founders & Sales Directors",
                "platforms": ["LINKEDIN", "X"],
                "core_idea": "80% of cold outbound fails because senders pitch services before understanding the prospect's tech stack and current bottlenecks.",
                "drafts": {
                    "LINKEDIN": "Most founders treat outbound like a lottery ticket: send 1,000 generic emails and hope 5 reply.\n\nHere is why that ruins your domain reputation and burns your addressable market:\n\n1. Zero pre-qualification\n2. Pitching features instead of pain relief\n3. Sending unsolicited follow-ups with no added value\n\nThe fix: Scrape verified signals first. Only reach out to companies where you have evidence of a current bottleneck.",
                    "X": "Treating cold outbound like a lottery ticket burns your domain and your TAM.\n\nStop blasting 1,000 generic pitches. Find 50 prospects with verified tech stack gaps and write 50 tailored notes.",
                },
            },
            {
                "title": "Architecture Breakdown: Building a 0-Crash AI Agent System",
                "pillar": "TECHNICAL_EXPERTISE",
                "target_audience": "Technical Architects & Engineers",
                "platforms": ["LINKEDIN", "REDDIT"],
                "core_idea": "How we designed a fault-tolerant multi-agent architecture using Python, SQLAlchemy 2.0, and offline heuristic NLP fallback when third-party APIs fail.",
                "drafts": {
                    "LINKEDIN": "If your AI application crashes when OpenAI or Gemini drops a 503, you don't have an operating system — you have a fragile API wrapper.\n\nHere is how we architected zero-crash resilience into our sales CRM:\n\n- Centralized Provider Health probes\n- Automatic multi-model failover\n- Deterministic offline heuristic NLP when all keys are missing",
                    "REDDIT": "Discussing resilient LLM architecture patterns: how do you prevent cascading system failures when upstream inference providers rate-limit or fail? Sharing our approach using local deterministic NLP fallbacks and connection health probes.",
                },
            },
        ]

        for s in samples:
            item = ContentItem(
                title=s["title"],
                pillar=s["pillar"],
                target_audience=s["target_audience"],
                platforms_json=json.dumps(s["platforms"]),
                core_idea=s["core_idea"],
                platform_drafts_json=json.dumps(s["drafts"]),
                status="APPROVED",
            )
            db.add(item)
        db.commit()
        logger.info("Seeded default content items.")
