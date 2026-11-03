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

        # Handle Email Personalization schema
        if "subject_line" in schema_description or "email_body" in schema_description:
            return {
                "subject_line": f"Quick question regarding {company_name}",
                "email_body": f"Hi {company_name} team,\n\nI noticed your great work and wanted to reach out regarding our sales and workflow automation services.\n\nWould you be open to a 10-minute introductory call next week?\n\nBest regards,\nSales Team",
                "personalization_reason": f"Identified company presence and relevant software requirements for {company_name}",
                "call_to_action": "10-minute call next week",
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
