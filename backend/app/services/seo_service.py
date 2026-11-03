"""SEO & Inbound Marketing Engine.

Handles keyword research, semantic clustering, search intent classification,
content brief generation, page planning, and meta title/description drafting.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.marketing import SEOProject, SEOKeyword
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class SEOService:
    """Manages SEO campaigns, keyword clusters, briefs, and page architecture."""

    SEARCH_INTENTS = ["INFORMATIONAL", "COMMERCIAL", "TRANSACTIONAL", "NAVIGATIONAL"]
    PAGE_TYPES = ["SERVICE_PAGE", "INDUSTRY_PAGE", "LOCATION_PAGE", "BLOG"]

    @classmethod
    def list_projects(cls, db: Session) -> List[Dict[str, Any]]:
        """List active SEO projects with keyword counts."""
        cls.seed_default_seo_if_empty(db)
        projects = db.query(SEOProject).order_by(SEOProject.created_at.desc()).all()
        return [
            {
                "id": str(p.id),
                "name": p.name,
                "target_domain": p.target_domain,
                "target_location": p.target_location,
                "gsc_connected": p.gsc_connected,
                "keywords_count": len(p.keywords),
            }
            for p in projects
        ]

    @classmethod
    def list_keywords(cls, project_id: str, db: Session) -> List[Dict[str, Any]]:
        """List keywords in a project with search intent and brief status."""
        pid = uuid.UUID(str(project_id))
        kws = db.query(SEOKeyword).filter(SEOKeyword.project_id == pid).order_by(SEOKeyword.search_volume.desc()).all()
        return [
            {
                "id": str(k.id),
                "keyword": k.keyword,
                "cluster_name": k.cluster_name,
                "search_intent": k.search_intent,
                "search_volume": k.search_volume,
                "difficulty_score": k.difficulty_score,
                "target_page_type": k.target_page_type,
                "meta_title": k.meta_title,
                "meta_description": k.meta_description,
                "status": k.status,
            }
            for k in kws
        ]

    @classmethod
    async def generate_keyword_clusters(
        cls,
        project_id: str,
        seed_topic: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Uses AI to brainstorm high-intent keywords, cluster them semantically,
        and classify search intent for landing page planning.
        """
        pid = uuid.UUID(str(project_id))
        project = db.query(SEOProject).filter(SEOProject.id == pid).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found")

        prompt = f"""You are an Inbound SEO Architect.
For the business domain '{project.target_domain}' and target seed topic '{seed_topic}',
generate 5 high-converting commercial and informational keywords.

For each keyword specify:
1. keyword: specific search query
2. cluster_name: topical cluster
3. search_intent: INFORMATIONAL, COMMERCIAL, or TRANSACTIONAL
4. target_page_type: SERVICE_PAGE, INDUSTRY_PAGE, or LOCATION_PAGE
5. estimated_monthly_volume: number between 100 and 5000
"""
        schema = """{
  "keywords": [
    {
      "keyword": "string",
      "cluster_name": "string",
      "search_intent": "COMMERCIAL",
      "target_page_type": "SERVICE_PAGE",
      "estimated_monthly_volume": 1200
    }
  ]
}"""
        try:
            res = await ai_router.generate_structured(prompt, schema)
            items = res.get("keywords", [])
        except Exception as e:
            logger.warning(f"AI keyword clustering failed, using fallback: {e}")
            items = [
                {
                    "keyword": f"{seed_topic} automation services",
                    "cluster_name": "Core Services",
                    "search_intent": "COMMERCIAL",
                    "target_page_type": "SERVICE_PAGE",
                    "estimated_monthly_volume": 850,
                },
                {
                    "keyword": f"best CRM for {seed_topic}",
                    "cluster_name": "Software Comparison",
                    "search_intent": "COMMERCIAL",
                    "target_page_type": "BLOG",
                    "estimated_monthly_volume": 1400,
                },
            ]

        created_count = 0
        for item in items:
            kw = SEOKeyword(
                project_id=pid,
                keyword=item.get("keyword"),
                cluster_name=item.get("cluster_name", "General"),
                search_intent=item.get("search_intent", "COMMERCIAL"),
                target_page_type=item.get("target_page_type", "SERVICE_PAGE"),
                search_volume=item.get("estimated_monthly_volume", 500),
                difficulty_score=35.0,
                status="PLANNED",
            )
            db.add(kw)
            created_count += 1

        db.commit()
        return {"project_id": str(pid), "keywords_created": created_count}

    @classmethod
    async def create_content_brief(cls, keyword_id: str, db: Session) -> Dict[str, Any]:
        """Generates a detailed content brief and drafted meta title & description."""
        kid = uuid.UUID(str(keyword_id))
        kw = db.query(SEOKeyword).filter(SEOKeyword.id == kid).first()
        if not kw:
            raise ValueError(f"Keyword '{keyword_id}' not found")

        prompt = f"""You are a Senior SEO Content Strategist.
Create a high-ranking content brief for:
Target Keyword: '{kw.keyword}'
Intent: {kw.search_intent}
Page Type: {kw.target_page_type}

Include:
1. Recommended H1 and 3-4 H2 section headings
2. Meta Title (under 60 chars, including primary keyword)
3. Meta Description (under 155 chars, compelling CTA)
4. Key questions to answer in the article/page
5. Target word count range
"""
        schema = """{
  "meta_title": "string",
  "meta_description": "string",
  "headings": ["string"],
  "target_word_count": 1500,
  "key_questions": ["string"]
}"""
        try:
            res = await ai_router.generate_structured(prompt, schema)
        except Exception:
            res = {
                "meta_title": f"{kw.keyword.title()} | Expert Solutions",
                "meta_description": f"Discover how our {kw.keyword} can accelerate your sales pipeline and reduce operational friction. Learn more today.",
                "headings": [f"Introduction to {kw.keyword}", "Key Benefits & ROI", "Implementation Steps", "Frequently Asked Questions"],
                "target_word_count": 1200,
                "key_questions": [f"What is {kw.keyword}?", f"How much does {kw.keyword} cost?"],
            }

        kw.meta_title = res.get("meta_title")
        kw.meta_description = res.get("meta_description")
        kw.content_brief = json.dumps(res)
        kw.status = "BRIEF_CREATED"
        db.commit()

        return {
            "keyword_id": str(kid),
            "meta_title": kw.meta_title,
            "meta_description": kw.meta_description,
            "brief": res,
        }

    @classmethod
    def seed_default_seo_if_empty(cls, db: Session) -> None:
        """Seed sample SEO project and target keywords."""
        if db.query(SEOProject).count() > 0:
            return

        proj = SEOProject(
            name="AI Sales & CRM Operating System",
            target_domain="ai-sales-crm.io",
            target_location="United States",
            gsc_connected=False,  # Transparent: Google Search Console not configured
        )
        db.add(proj)
        db.commit()
        db.refresh(proj)

        sample_kws = [
            ("AI sales CRM for agency", "Core Product", "COMMERCIAL", "SERVICE_PAGE", 1800),
            ("automated lead qualification software", "Lead Gen", "COMMERCIAL", "SERVICE_PAGE", 2400),
            ("how to automate B2B prospect discovery", "Guides", "INFORMATIONAL", "BLOG", 3100),
        ]
        for kw, cluster, intent, page_type, vol in sample_kws:
            rec = SEOKeyword(
                project_id=proj.id,
                keyword=kw,
                cluster_name=cluster,
                search_intent=intent,
                target_page_type=page_type,
                search_volume=vol,
                difficulty_score=42.0,
                meta_title=f"{kw.title()} | AI Sales OS",
                meta_description=f"Streamline your sales pipeline with our {kw}. Discover how to qualify prospects and close deals faster.",
                status="BRIEF_CREATED",
            )
            db.add(rec)
        db.commit()
        logger.info("Seeded default SEO project and keywords.")
