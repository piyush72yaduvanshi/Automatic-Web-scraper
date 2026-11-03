"""AI Intelligence Service supporting Google Gemini, OpenRouter, and Algorithmic Heuristics."""

from typing import Dict, Any, List, Optional
import json
import re
import httpx

from app.core.config import settings


class AIService:
    """
    Intelligent AI analysis and extraction engine.
    Supports Google Gemini API, OpenRouter API, and Heuristic NLP Fallback.
    """

    @classmethod
    def is_configured(cls, custom_key: Optional[str] = None) -> bool:
        """Check if any AI provider is configured."""
        return bool(custom_key or settings.GEMINI_API_KEY or settings.OPENROUTER_API_KEY)

    @classmethod
    async def analyze_and_extract(
        cls,
        business_name: str,
        category: Optional[str],
        location: Optional[str],
        website_content: Optional[str] = None,
        search_snippets: Optional[List[str]] = None,
        raw_contacts: Optional[Dict[str, Any]] = None,
        custom_ai_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze multi-source aggregated text using Gemini or OpenRouter,
        falling back to high-accuracy algorithmic heuristic extraction.
        """
        # Prepare aggregated context
        snippets_text = "\n".join(search_snippets or [])[:4000]
        site_text = (website_content or "")[:6000]
        
        # If Gemini or OpenRouter key is available, call LLM
        gemini_key = custom_ai_key or settings.GEMINI_API_KEY
        openrouter_key = custom_ai_key if (custom_ai_key and custom_ai_key.startswith("sk-or-")) else settings.OPENROUTER_API_KEY

        if gemini_key and not gemini_key.startswith("sk-or-"):
            try:
                result = await cls._call_gemini(gemini_key, business_name, category, location, site_text, snippets_text, raw_contacts)
                if result:
                    return result
            except Exception as e:
                print(f"[AIService] Gemini API error: {e}, falling back to heuristic...")

        elif openrouter_key:
            try:
                result = await cls._call_openrouter(openrouter_key, business_name, category, location, site_text, snippets_text, raw_contacts)
                if result:
                    return result
            except Exception as e:
                print(f"[AIService] OpenRouter API error: {e}, falling back to heuristic...")

        # Algorithmic NLP heuristic fallback
        return cls._heuristic_analysis(business_name, category, location, site_text, search_snippets, raw_contacts)

    @classmethod
    async def _call_gemini(
        cls,
        api_key: str,
        name: str,
        category: Optional[str],
        location: Optional[str],
        site_text: str,
        snippets_text: str,
        raw_contacts: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Call Google Gemini 1.5/2.0 Flash REST API directly."""
        prompt = cls._build_extraction_prompt(name, category, location, site_text, snippets_text, raw_contacts)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        return None

    @classmethod
    async def _call_openrouter(
        cls,
        api_key: str,
        name: str,
        category: Optional[str],
        location: Optional[str],
        site_text: str,
        snippets_text: str,
        raw_contacts: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Call OpenRouter chat completions API."""
        prompt = cls._build_extraction_prompt(name, category, location, site_text, snippets_text, raw_contacts)
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://lead-discovery-crm.local",
            "X-Title": "CRM Lead Discovery",
        }

        payload = {
            "model": settings.OPENROUTER_MODEL or "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": "You are a professional B2B lead intelligence and contact extraction specialist. Always respond with pure JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        return None

    @classmethod
    def _build_extraction_prompt(
        cls,
        name: str,
        category: Optional[str],
        location: Optional[str],
        site_text: str,
        snippets_text: str,
        raw_contacts: Optional[Dict[str, Any]],
    ) -> str:
        """Construct the extraction prompt for the AI."""
        return f"""You are analyzing a business for CRM lead discovery.
Business Name: {name}
Category: {category or 'Unknown'}
Location: {location or 'Unknown'}

Raw Contact Candidates:
{json.dumps(raw_contacts or {}, indent=2)}

Website Text Snippets:
{site_text[:2500]}

Search Snippets:
{snippets_text[:2000]}

Extract and return ONLY a valid JSON object matching this schema:
{{
  "summary": "1-2 sentence compelling summary of what the business does and their main services",
  "key_people": [
    {{"name": "Full Name", "role": "e.g. Founder, Chief Dentist, Director, Manager"}}
  ],
  "verified_emails": [
    {{"email": "contact@domain.com", "label": "e.g. Inquiries, Personal, Support", "confidence": "high"}}
  ],
  "verified_phones": [
    {{"phone": "+91...", "label": "e.g. Office, WhatsApp, Mobile", "confidence": "high"}}
  ],
  "social_profiles": {{
    "LINKEDIN": "https://...",
    "INSTAGRAM": "https://...",
    "FACEBOOK": "https://...",
    "X": "https://..."
  }},
  "quality_score": 85,
  "quality_reason": "Brief reason for this score (0-100)"
}}
Ensure quality_score is an integer between 0 and 100 based on the richness and authenticity of available contact data."""

    @classmethod
    def _heuristic_analysis(
        cls,
        name: str,
        category: Optional[str],
        location: Optional[str],
        site_text: str,
        search_snippets: Optional[List[str]],
        raw_contacts: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        High accuracy rule-based heuristic intelligence engine.
        Runs when LLM keys are absent, ensuring instantaneous zero-cost performance.
        """
        all_text = f"{name} {category or ''} {site_text} {' '.join(search_snippets or [])}"
        
        # 1. Identify key people / doctor / founder names
        key_people = []
        name_patterns = [
            r'(?:Dr\.|Doctor|Dr)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'(?:Founder|CEO|Director|Owner|Proprietor|Head Dentist)[:\s-]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*[-–,]\s*(?:Founder|CEO|Director|Owner|BDS|MDS|MBBS)',
        ]
        seen_people = set()
        for pat in name_patterns:
            for match in re.finditer(pat, all_text):
                p_name = match.group(1).strip()
                if len(p_name.split()) >= 2 and p_name.lower() not in seen_people:
                    # Ignore common generic strings
                    if not any(w in p_name.lower() for w in ['dental', 'clinic', 'hospital', 'care', 'center', 'india', 'service']):
                        seen_people.add(p_name.lower())
                        key_people.append({
                            "name": p_name,
                            "role": "Founder / Key Executive"
                        })
                if len(key_people) >= 3:
                    break

        # 2. Extract and categorize verified emails
        raw_emails = (raw_contacts or {}).get("emails", [])
        verified_emails = []
        for em in raw_emails:
            e_str = em if isinstance(em, str) else em.get("email", "")
            if e_str:
                label = "General"
                if any(k in e_str for k in ["info", "contact", "support"]):
                    label = "Support / Inquiries"
                elif any(k in e_str for k in ["sales", "care", "help"]):
                    label = "Customer Care"
                else:
                    label = "Direct / Executive"
                verified_emails.append({
                    "email": e_str,
                    "label": label,
                    "confidence": "high"
                })

        # 3. Extract verified phones
        raw_phones = (raw_contacts or {}).get("phones", [])
        verified_phones = []
        for ph in raw_phones:
            p_val = ph if isinstance(ph, str) else (ph.get("normalized") or ph.get("original", ""))
            if p_val:
                verified_phones.append({
                    "phone": p_val,
                    "label": "Phone / Mobile",
                    "confidence": "high"
                })

        # 4. Extract socials
        socials = {}
        raw_socials = (raw_contacts or {}).get("social_profiles", [])
        for soc in raw_socials:
            if isinstance(soc, dict):
                p = soc.get("platform")
                u = soc.get("url")
                if p and u:
                    socials[p] = u

        # 5. Compute Lead Quality Score (0-100)
        score = 30  # Baseline for discovered business
        reasons = []

        if verified_phones:
            score += 25
            reasons.append(f"{len(verified_phones)} phone(s)")
        if verified_emails:
            score += 25
            reasons.append(f"{len(verified_emails)} email(s)")
        if socials:
            score += 15
            reasons.append(f"{len(socials)} social profile(s)")
        if key_people:
            score += 10
            reasons.append("Key decision maker identified")
        if (raw_contacts or {}).get("website"):
            score += 10
            reasons.append("Verified web presence")

        score = min(100, max(20, score))
        summary = f"{name} is an established {category or 'business'} based in {location or 'India'}, providing professional services with verified contact channels."

        return {
            "summary": summary,
            "key_people": key_people,
            "verified_emails": verified_emails,
            "verified_phones": verified_phones,
            "social_profiles": socials,
            "quality_score": score,
            "quality_reason": ", ".join(reasons) if reasons else "Basic listing profile"
        }

