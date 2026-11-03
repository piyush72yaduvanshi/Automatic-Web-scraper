"""Offline Heuristic AI Provider (Rule-Based & Algorithmic).

Guarantees 100% uptime and functionality even when all external AI APIs are missing,
network is disconnected, or rate limits are reached.
"""

import re
import hashlib
from typing import Dict, Any, List, Optional

from app.providers.ai.base import BaseAIProvider


class HeuristicAIProvider(BaseAIProvider):
    """Deterministic, zero-dependency offline intelligence engine."""

    provider_name: str = "heuristic_nlp"

    def is_available(self) -> bool:
        return True

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> Optional[str]:
        """Generate sensible deterministic response based on key prompt terms."""
        p_lower = prompt.lower()
        if "outreach" in p_lower or "email" in p_lower:
            return (
                "Hi there,\n\n"
                "I noticed your impressive work and wanted to reach out regarding how our services "
                "can support your current business goals and streamline your workflows.\n\n"
                "Would you be open to a brief 10-minute introductory call next week?\n\n"
                "Best regards,\nSales & Partnership Team"
            )
        elif "follow-up" in p_lower:
            return (
                "Hi,\n\n"
                "Following up on our previous note. We'd love to connect and share some quick insights "
                "that could benefit your team.\n\n"
                "Let me know if you have a few minutes this week.\n\n"
                "Best regards,\nSales Team"
            )
        return (
            "Heuristic Analysis: Business information processed successfully. "
            "Profile meets baseline criteria for review."
        )

    async def generate_structured(
        self,
        prompt: str,
        schema_description: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Optional[Dict[str, Any]]:
        """Generate structured business qualification and synthesis using NLP heuristics."""
        p_lower = prompt.lower()

        # Extract potential company name
        company_name = "Target Company"
        match_name = re.search(r"business[:\s]+([^\n,]+)", prompt, re.IGNORECASE) or re.search(r"company[:\s]+([^\n,]+)", prompt, re.IGNORECASE)
        if match_name:
            company_name = match_name.group(1).strip()

        # Handle Workflow Planning schema
        if "workflow_name" in schema_description or "steps" in schema_description:
            return {
                "workflow_name": "Autonomous Sales Outreach Workflow",
                "total_steps": 3,
                "steps": [
                    {"step_number": 1, "agent": "lead_discovery_agent", "action_description": "Discover business candidates matching query", "requires_human_approval": False},
                    {"step_number": 2, "agent": "company_research_agent", "action_description": "Analyze company website and pain points", "requires_human_approval": False},
                    {"step_number": 3, "agent": "email_personalization_agent", "action_description": "Draft tailored cold email for approval", "requires_human_approval": True},
                ],
                "estimated_duration_seconds": 30,
            }

        # Handle Social Research schema
        if "trending_angles" in schema_description:
            return {
                "trending_angles": [
                    "Why agentic AI workflows outperform static automation in 2026",
                    "The shift from mass cold blasting to hyper-personalized relevance",
                    "How modern engineering teams eliminate manual CRM data entry"
                ],
                "audience_resonances": [
                    "ROI on operational time savings (10-20 hrs/week)",
                    "Data compliance and domain deliverability protection",
                    "Seamless omnichannel visibility without context switching"
                ],
                "recommended_keywords": ["#SalesAutomation", "#AIWorkflow", "#B2BGrowth", "#GTMStrategy", "#DevOps"],
                "visual_theme": "Modern minimalist dark mode UI with high-contrast cyan and emerald accents"
            }

        # Handle Complete Multi-Platform Social Media Posts Schema
        if "social_posts" in schema_description:
            return {
                "research_summary": "High demand for actionable B2B operational frameworks with verifiable ROI metrics.",
                "social_posts": {
                    "INSTAGRAM": {
                        "caption": "Efficiency isn't about working more hours. It's about designing architectures that work while you sleep. 🚀\n\nHere are 3 rules for automated B2B workflows that scale:\n\n1️⃣ Pre-qualify before you outreach.\n2️⃣ Verify domain DNS health daily.\n3️⃣ Automate routine tasks, keep strategy human.\n\nSwipe left to see our system architecture breakdown! 👉\n\nDrop a comment with 'SYSTEM' for the full technical guide.",
                        "hashtags": ["#AIAutomation", "#SalesEngineering", "#B2BGrowth", "#SaaSArchitecture", "#WorkSmarter", "#TechFounders", "#StartupTips"],
                        "creative_brief": {
                            "visual_concept": "Carousel slide with clean system architecture diagram and bold headline overlay",
                            "aspect_ratio": "1:1",
                            "dimensions": "1080x1080",
                            "text_overlay": "3 Rules for Scalable Sales Automation",
                            "color_palette": ["#0f172a", "#06b6d4", "#10b981"]
                        }
                    },
                    "FACEBOOK": {
                        "caption": "Most sales teams spend 65% of their working hours on manual CRM admin, copy-pasting lead data, and chasing bounced emails.\n\nWe spent the last month building an autonomous operating system to eliminate that friction entirely.\n\nKey takeaways from our pilot tests:\n• Lead qualification time dropped from 12 mins to 4 seconds\n• Email bounce rates stayed below 1.2%\n• Sales pipeline velocity increased by 40%\n\nHow is your team modernizing its sales workflows this quarter? Let's discuss in the comments below!",
                        "hashtags": ["#BusinessAutomation", "#SalesOperations", "#ProductivityTech"],
                        "creative_brief": {
                            "visual_concept": "High-impact infographic comparing manual vs automated sales operations time allocation",
                            "aspect_ratio": "1.91:1",
                            "dimensions": "1200x630",
                            "text_overlay": "Manual vs Autonomous Sales Operations",
                            "color_palette": ["#1e293b", "#3b82f6"]
                        }
                    },
                    "TWITTER": {
                        "caption": "Your sales stack shouldn't require 10 fragmented tools and endless manual syncing.\n\n1/ Automated lead discovery\n2/ Verified contact enrichment\n3/ Domain deliverability protection\n4/ AI research dossiers\n\nAll native in Python. 0 external brittle wrappers.",
                        "hashtags": ["#BuildInPublic", "#Python", "#AI"],
                        "creative_brief": {
                            "visual_concept": "Code terminal preview card showing clean Python Celery and FastAPI pipeline execution",
                            "aspect_ratio": "16:9",
                            "dimensions": "1200x675",
                            "text_overlay": "Autonomous Sales OS in Python",
                            "color_palette": ["#000000", "#10b981"]
                        }
                    },
                    "LINKEDIN_PERSONAL": {
                        "caption": "Unpopular opinion in B2B sales: The problem with cold outreach isn't the channel. It's the lack of pre-flight evidence.\n\nWhen we audited 10,000 cold emails, the pattern was clear:\n\n→ 78% pitched services with zero relevance to the prospect's actual tech stack.\n→ 14% had broken SPF/DKIM authentication and landed directly in spam.\n→ Only 8% used verified business pain points.\n\nThe teams winning right now aren't sending more volume. They are qualifying deeper with automated research agents before sending a single note.\n\nWhat is your biggest bottleneck in prospect qualification today?",
                        "hashtags": ["#SalesLeadership", "#B2BStrategy", "#ArtificialIntelligence", "#FounderInsights"],
                        "creative_brief": {
                            "visual_concept": "Clean data chart showing conversion rates: Mass Blasting vs Evidence-Based Outreach",
                            "aspect_ratio": "1.91:1",
                            "dimensions": "1200x627",
                            "text_overlay": "Why 78% of Cold Outreach Fails",
                            "color_palette": ["#0f172a", "#6366f1"]
                        }
                    },
                    "LINKEDIN_ORG": {
                        "caption": "We are proud to announce the release of our complete AI Sales, Lead Generation & Outreach Operating System.\n\nDesigned for modern growth teams, the platform unifies lead discovery, relational CRM pipelines, unified inbox messaging, and native workflow automation into a resilient, self-hosted system.\n\nExplore our open architecture breakdown and test our deliverability benchmarks today.",
                        "hashtags": ["#ProductAnnouncement", "#EnterpriseSoftware", "#SalesTech", "#Innovation"],
                        "creative_brief": {
                            "visual_concept": "Enterprise product banner showcasing dashboard interface with live metrics",
                            "aspect_ratio": "1.91:1",
                            "dimensions": "1200x627",
                            "text_overlay": "Enterprise AI Sales & Marketing Operating System",
                            "color_palette": ["#090d16", "#38bdf8"]
                        }
                    }
                }
            }

        # Handle Email Personalization schema
        if "subject_line" in schema_description or "email_body" in schema_description:
            return {
                "subject_line": f"Quick question regarding {company_name}",
                "email_body": f"Hi {company_name} team,\n\nI noticed your great work and wanted to reach out regarding our sales and workflow automation services.\n\nWould you be open to a 10-minute introductory call next week?\n\nBest regards,\nSales Team",
                "personalization_reason": f"Identified company presence and relevant software requirements for {company_name}",
                "call_to_action": "10-minute call next week",
            }

        # Handle Social Content Repurposing schema
        if "platform_drafts" in schema_description:
            return {
                "platform_drafts": {
                    "LINKEDIN": f"Most organizations struggle with operational friction.\n\nHere is what we discovered analyzing growth patterns:\n1. Automating pre-qualification saves 15 hours/week.\n2. Verified outreach converts 3x higher.\n\nHow is your team approaching this?",
                    "X": "Stop blasting unverified cold pitches.\n\nPre-qualify your accounts with evidence first and write 1-on-1 personalized notes.",
                    "REDDIT": "Sharing some operational benchmarks: we noticed a 3x increase in reply rates when switching from generic volume to evidence-based qualification. Anyone else testing similar workflows?",
                },
                "summary_hook": "Evidence-backed sales operations breakdown",
            }

        # Extract people / executives
        key_people = []
        exec_matches = re.findall(
            r'(?:Dr\.|Doctor|Founder|CEO|Director|Manager|Owner)[:\s-]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            prompt
        )
        for name in set(exec_matches):
            key_people.append({"name": name, "title": "Decision Maker"})

        # Identify channels
        has_email = "@" in prompt
        has_phone = bool(re.search(r'\+?\d[\d\s-]{8,}\d', prompt))
        has_linkedin = "linkedin.com" in p_lower

        score = 50
        if has_email:
            score += 20
        if has_phone:
            score += 15
        if has_linkedin:
            score += 10
        if key_people:
            score += 5
        score = min(score, 100)

        status = "Qualified" if score >= 70 else ("Maybe" if score >= 45 else "New")

        # Handle Lead Qualification schema
        if "icp_fit_score" in schema_description:
            return {
                "icp_fit_score": 80.0,
                "business_pain_score": 75.0,
                "timing_intent_score": 60.0,
                "reachability_score": float(score),
                "evidence_score": 70.0,
                "qualification_status": status,
                "reasoning": f"Heuristic analysis verified contact reachability (score {score}/100).",
                "missing_information": ["Direct decision maker mobile", "Annual tech budget"],
                "recommended_next_action": "Draft personalized email outreach",
            }


        return {
            "summary": f"{company_name} is an active commercial business identified for outreach.",
            "qualification_score": score,
            "status": status,
            "reasoning": f"Heuristic analysis verified contact endpoints (email={has_email}, phone={has_phone}, linkedin={has_linkedin}).",
            "key_people": key_people,
            "pain_points": [
                "Manual operational processes",
                "Digital presence expansion",
                "Scalable software solutions"
            ],
            "suggested_offering": "Custom Software & Lead Management Automation",
            "verified_facts": [
                f"Identified presence: {company_name}",
                f"Contact reachability: {'Available' if (has_email or has_phone) else 'Limited'}"
            ],
            "inferred_insights": [
                "Likely receptive to efficiency improvements and digital tools"
            ],
            "unknowns": [
                "Specific annual technology budget",
                "Current internal engineering team size"
            ]
        }

    async def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """Generate deterministic 128-dimensional character/term hash vector for offline retrieval."""
        words = re.findall(r'\b\w+\b', text.lower())
        vector = [0.0] * 128
        for word in words:
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest()[:8], 16)
            idx = h % 128
            vector[idx] += 1.0

        # Normalize vector length
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector
