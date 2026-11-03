"""Multi-Source Enrichment Engine combining Firecrawl, Direct Web Scraping, Search Radar, and AI."""

from typing import Dict, Any, List, Optional
import asyncio
import json
import re
import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.extractors import EmailExtractor, PhoneExtractor, SocialExtractor
from app.providers.enrichment.firecrawl_provider import FirecrawlProvider
from app.providers.enrichment.search_radar import SearchRadarProvider
from app.services.ai_service import AIService


class MultiSourceEnricher:
    """
    Coordinates enrichment across multiple independent sources:
    - Official website deep crawl (Firecrawl + Direct scraping + JSON-LD)
    - Search Radar (Google Search foot-printing for socials & missing contacts)
    - AI Intelligence (Gemini / OpenRouter for decision makers, validation, scoring)
    """

    def __init__(self):
        self.firecrawl = FirecrawlProvider()
        self.search_radar = SearchRadarProvider()

    async def enrich_lead(
        self,
        business_name: str,
        website: Optional[str] = None,
        category: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        existing_phone: Optional[str] = None,
        custom_ai_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enrich a lead using multiple parallel sources and AI synthesis.
        """
        all_emails: List[Dict[str, Any]] = []
        all_phones: List[Dict[str, Any]] = []
        all_socials: List[Dict[str, Any]] = []
        evidence_records: List[Dict[str, Any]] = []
        raw_snippets: List[str] = []
        website_text: str = ""

        # If phone was already provided by discovery (e.g. from Google Maps card)
        if existing_phone:
            normalized = PhoneExtractor.normalize_phone(existing_phone)
            all_phones.append({
                "original": existing_phone,
                "normalized": normalized or existing_phone,
                "source_url": "https://maps.google.com",
                "verification_status": "verified",
            })
            evidence_records.append({
                "field_name": "phone",
                "extracted_value": existing_phone,
                "source_url": "https://maps.google.com",
                "provider": "google_maps",
            })

        # Tasks for concurrent execution
        tasks = []

        # 1. Website Crawl Task (if website is available)
        if website:
            tasks.append(self._crawl_website(website))
        else:
            tasks.append(asyncio.sleep(0, result=None))

        # 2. Search Engine Footprint Task
        if self.search_radar.is_configured():
            tasks.append(self.search_radar.scan_business_footprint(
                business_name=business_name,
                city=city,
                state=state,
            ))
        else:
            tasks.append(asyncio.sleep(0, result=None))

        # Run multi-source extractions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        web_res = results[0] if len(results) > 0 and not isinstance(results[0], Exception) else None
        radar_res = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else None

        # Process Website Crawl Results
        if web_res:
            site_emails = web_res.get("emails", [])
            site_phones = web_res.get("phones", [])
            site_socials = web_res.get("social_profiles", [])
            website_text = web_res.get("raw_text", "")

            for em in site_emails:
                all_emails.append(em)
                evidence_records.append({
                    "field_name": "email",
                    "extracted_value": em.get("email"),
                    "source_url": em.get("source_url", website),
                    "provider": "website_crawl",
                })

            for ph in site_phones:
                all_phones.append(ph)
                evidence_records.append({
                    "field_name": "phone",
                    "extracted_value": ph.get("normalized") or ph.get("original"),
                    "source_url": ph.get("source_url", website),
                    "provider": "website_crawl",
                })

            for soc in site_socials:
                all_socials.append(soc)
                evidence_records.append({
                    "field_name": "social_profile",
                    "extracted_value": soc.get("url"),
                    "source_url": soc.get("source_url", website),
                    "provider": "website_crawl",
                })

        # Process Search Radar Results
        if radar_res:
            radar_emails = radar_res.get("emails", [])
            radar_phones = radar_res.get("phones", [])
            radar_socials = radar_res.get("social_profiles", [])
            raw_snippets = radar_res.get("snippets", [])

            for em in radar_emails:
                all_emails.append(em)
                evidence_records.append({
                    "field_name": "email",
                    "extracted_value": em.get("email"),
                    "source_url": em.get("source_url"),
                    "provider": "search_radar",
                })

            for ph in radar_phones:
                all_phones.append(ph)
                evidence_records.append({
                    "field_name": "phone",
                    "extracted_value": ph.get("normalized") or ph.get("original"),
                    "source_url": ph.get("source_url"),
                    "provider": "search_radar",
                })

            for soc in radar_socials:
                all_socials.append(soc)
                evidence_records.append({
                    "field_name": "social_profile",
                    "extracted_value": soc.get("url"),
                    "source_url": soc.get("source_url"),
                    "provider": "search_radar",
                })

        # Deduplicate contacts
        unique_emails = EmailExtractor.deduplicate(all_emails)
        unique_phones = PhoneExtractor.deduplicate(all_phones)
        unique_socials = SocialExtractor.deduplicate(all_socials)

        # 3. AI Intelligence Synthesis (Gemini / OpenRouter / Heuristic)
        raw_contact_payload = {
            "website": website,
            "emails": unique_emails,
            "phones": unique_phones,
            "social_profiles": unique_socials,
        }

        ai_insights = await AIService.analyze_and_extract(
            business_name=business_name,
            category=category,
            location=f"{city or ''}, {state or ''}".strip(),
            website_content=website_text,
            search_snippets=raw_snippets,
            raw_contacts=raw_contact_payload,
            custom_ai_key=custom_ai_key,
        )

        # Merge any additional contacts identified by AI
        for v_em in ai_insights.get("verified_emails", []):
            em_val = v_em.get("email", "").lower()
            if em_val and not any(e.get("email", "").lower() == em_val for e in unique_emails):
                unique_emails.append({
                    "email": em_val,
                    "source_url": website or "ai_analysis",
                    "verification_status": "ai_verified",
                })

        for v_ph in ai_insights.get("verified_phones", []):
            ph_val = v_ph.get("phone", "")
            norm = PhoneExtractor.normalize_phone(ph_val) or ph_val
            if norm and not any(p.get("normalized") == norm for p in unique_phones):
                unique_phones.append({
                    "original": ph_val,
                    "normalized": norm,
                    "source_url": website or "ai_analysis",
                    "verification_status": "ai_verified",
                })

        for platform, url in ai_insights.get("social_profiles", {}).items():
            if url and not any(s.get("url") == url for s in unique_socials):
                unique_socials.append({
                    "platform": platform,
                    "url": url,
                    "source_url": "ai_analysis",
                    "verification_status": "ai_verified",
                })

        sources_consulted = []
        if website:
            sources_consulted.append("Website Deep Crawl")
        if radar_res and raw_snippets:
            sources_consulted.append("SerpAPI Social Radar")
        if AIService.is_configured(custom_ai_key):
            sources_consulted.append("Gemini/OpenRouter AI")
        else:
            sources_consulted.append("AI Pattern Engine")

        return {
            "emails": unique_emails,
            "phones": unique_phones,
            "social_profiles": unique_socials,
            "evidence": evidence_records,
            "ai_insights": ai_insights,
            "quality_score": ai_insights.get("quality_score", 50),
            "summary": ai_insights.get("summary"),
            "key_people": ai_insights.get("key_people", []),
            "sources_consulted": sources_consulted,
        }

    async def _crawl_website(self, website_url: str) -> Dict[str, Any]:
        """
        Deep crawl website combining Firecrawl API with direct parsing fallback.
        Also parses JSON-LD schema objects for contact details.
        """
        # Ensure scheme
        if not website_url.startswith(("http://", "https://")):
            website_url = "https://" + website_url

        all_emails = []
        all_phones = []
        all_socials = []
        raw_text_parts = []

        try:
            # 1. First, attempt standard Firecrawl enrich with strict 8s timeout
            if self.firecrawl.is_configured():
                try:
                    fc_res = await asyncio.wait_for(self.firecrawl.enrich_website(website_url), timeout=8.0)
                    all_emails.extend(fc_res.get("emails", []))
                    all_phones.extend(fc_res.get("phones", []))
                    all_socials.extend(fc_res.get("social_profiles", []))
                except Exception as fc_err:
                    print(f"[MultiSourceEnricher] Firecrawl timeout/error for {website_url}: {fc_err}")

            # 2. In addition, fetch homepage directly to extract JSON-LD and clean text
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                resp = await client.get(
                    website_url,
                    headers={"User-Agent": settings.USER_AGENT},
                )
                if resp.status_code == 200:
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")
                    raw_text_parts.append(soup.get_text(separator=" ", strip=True)[:3000])

                    # Extract JSON-LD Schemas (LocalBusiness, Organization, etc.)
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            schema = json.loads(script.string or "{}")
                            if isinstance(schema, dict):
                                self._extract_from_json_ld(schema, website_url, all_emails, all_phones, all_socials)
                            elif isinstance(schema, list):
                                for s_item in schema:
                                    if isinstance(s_item, dict):
                                        self._extract_from_json_ld(s_item, website_url, all_emails, all_phones, all_socials)
                        except Exception:
                            pass

                    # Extract emails, phones, socials from homepage direct HTML
                    all_emails.extend(EmailExtractor.extract_from_html(html, website_url))
                    all_phones.extend(PhoneExtractor.extract_from_html(html, website_url))
                    all_socials.extend(SocialExtractor.extract_from_html(html, website_url))

        except Exception as e:
            print(f"[MultiSourceEnricher] Direct scrape failed for {website_url}: {e}")

        return {
            "emails": EmailExtractor.deduplicate(all_emails),
            "phones": PhoneExtractor.deduplicate(all_phones),
            "social_profiles": SocialExtractor.deduplicate(all_socials),
            "raw_text": " ".join(raw_text_parts),
        }

    def _extract_from_json_ld(
        self,
        schema: Dict[str, Any],
        source_url: str,
        emails: List[Dict[str, Any]],
        phones: List[Dict[str, Any]],
        socials: List[Dict[str, Any]],
    ) -> None:
        """Extract telephone, email, and sameAs social links from JSON-LD schema."""
        # Email in schema
        em = schema.get("email")
        if em and isinstance(em, str) and "@" in em:
            emails.append({"email": em.lower(), "source_url": source_url, "verification_status": "schema_verified"})

        # Telephone in schema
        tel = schema.get("telephone")
        if tel and isinstance(tel, str):
            norm = PhoneExtractor.normalize_phone(tel)
            phones.append({"original": tel, "normalized": norm or tel, "source_url": source_url, "verification_status": "schema_verified"})

        # Social links in sameAs
        same_as = schema.get("sameAs")
        if isinstance(same_as, list):
            for link in same_as:
                if isinstance(link, str):
                    socs = SocialExtractor.extract_from_html(f'<a href="{link}">social</a>', source_url)
                    socials.extend(socs)
        elif isinstance(same_as, str):
            socs = SocialExtractor.extract_from_html(f'<a href="{same_as}">social</a>', source_url)
            socials.extend(socs)

