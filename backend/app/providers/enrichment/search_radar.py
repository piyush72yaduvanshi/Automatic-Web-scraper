"""Search Radar provider for extracting social footprints and contacts via web search."""

from typing import Dict, Any, List, Optional
import httpx
import re

from app.core.config import settings
from app.extractors import EmailExtractor, PhoneExtractor, SocialExtractor


class SearchRadarProvider:
    """
    Leverages SerpAPI search engine to locate social media profiles,
    directory mentions, public emails, and contact numbers.
    """

    def __init__(self):
        self.api_key = settings.SERPAPI_API_KEY or settings.SEARCH_API_KEY
        self.timeout = settings.SEARCH_API_TIMEOUT
        self.base_url = "https://serpapi.com/search"

    def is_configured(self) -> bool:
        """Check if search API key is configured."""
        return bool(self.api_key)

    async def scan_business_footprint(
        self,
        business_name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        extract_emails: bool = True,
        extract_phones: bool = True,
        extract_socials: bool = True,
    ) -> Dict[str, Any]:
        """
        Scan search engine results for contact footprints and social URLs.
        """
        if not self.is_configured():
            return {"emails": [], "phones": [], "social_profiles": [], "snippets": []}

        loc = f"{city or ''} {state or ''}".strip()
        search_query = f"{business_name} {loc} contact email linkedin instagram facebook"

        params = {
            "engine": "google",
            "q": search_query,
            "api_key": self.api_key,
            "num": 8,
        }

        all_emails = []
        all_phones = []
        all_socials = []
        snippets = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    return {"emails": [], "phones": [], "social_profiles": [], "snippets": []}

                data = resp.json()
                results = data.get("organic_results", [])

                for item in results:
                    link = item.get("link", "")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    full_text = f"{title} {snippet} {link}"
                    snippets.append(full_text)

                    # 1. Social Extraction from URLs and snippets
                    if extract_socials:
                        social_found = SocialExtractor.extract_from_html(f'<a href="{link}">{title}</a> {snippet}', link)
                        all_socials.extend(social_found)

                    # 2. Email Extraction from snippet text
                    if extract_emails and snippet:
                        emails_found = EmailExtractor.extract_from_text(snippet, link)
                        all_emails.extend(emails_found)

                    # 3. Phone Extraction from snippet text
                    if extract_phones and snippet:
                        phones_found = PhoneExtractor.extract_from_text(snippet, link)
                        all_phones.extend(phones_found)

        except Exception as e:
            print(f"[SearchRadar] Error scanning footprint for {business_name}: {e}")

        return {
            "emails": EmailExtractor.deduplicate(all_emails),
            "phones": PhoneExtractor.deduplicate(all_phones),
            "social_profiles": SocialExtractor.deduplicate(all_socials),
            "snippets": snippets,
        }

