"""Firecrawl website enrichment provider."""

from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.core.security import is_safe_url, sanitize_url
from app.extractors import EmailExtractor, PhoneExtractor, SocialExtractor


class FirecrawlProvider:
    """
    Firecrawl provider for website content extraction.
    
    Uses Firecrawl API to extract content from business websites.
    """
    
    def __init__(self):
        self.api_key = settings.FIRECRAWL_API_KEY
        self.timeout = settings.FIRECRAWL_REQUEST_TIMEOUT
        self.max_pages = settings.FIRECRAWL_MAX_PAGES
        self.base_url = "https://api.firecrawl.dev/v0"
    
    def is_configured(self) -> bool:
        """Check if Firecrawl API key is configured."""
        return bool(self.api_key)
    
    async def enrich_website(
        self,
        website_url: str,
        extract_emails: bool = True,
        extract_phones: bool = True,
        extract_socials: bool = True,
    ) -> Dict[str, Any]:
        """
        Enrich website by extracting contact information.
        
        Args:
            website_url: Business website URL
            extract_emails: Extract email addresses
            extract_phones: Extract phone numbers
            extract_socials: Extract social profiles
            
        Returns:
            Dictionary with extracted data
        """
        # Sanitize and validate URL
        website_url = sanitize_url(website_url)
        is_safe, error = is_safe_url(website_url)
        if not is_safe:
            raise ValueError(f"Unsafe URL: {error}")
        
        # Extract base domain
        from urllib.parse import urlparse
        parsed = urlparse(website_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Define pages to crawl
        pages_to_crawl = [
            website_url,
            f"{base_url}/contact",
            f"{base_url}/contact-us",
            f"{base_url}/about",
            f"{base_url}/about-us",
        ]
        
        all_emails = []
        all_phones = []
        all_socials = []
        
        # Crawl each page
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for page_url in pages_to_crawl[:self.max_pages]:
                try:
                    content = await self._scrape_page(client, page_url)
                    
                    if content:
                        # Extract data
                        if extract_emails:
                            emails = EmailExtractor.extract_from_html(content, page_url)
                            all_emails.extend(emails)
                        
                        if extract_phones:
                            phones = PhoneExtractor.extract_from_html(content, page_url)
                            all_phones.extend(phones)
                        
                        if extract_socials:
                            socials = SocialExtractor.extract_from_html(content, page_url)
                            all_socials.extend(socials)
                
                except Exception as e:
                    # Log error but continue with other pages
                    print(f"Error crawling {page_url}: {str(e)}")
                    continue
        
        # Deduplicate
        unique_emails = EmailExtractor.deduplicate(all_emails)
        unique_phones = PhoneExtractor.deduplicate(all_phones)
        unique_socials = SocialExtractor.deduplicate(all_socials)
        
        return {
            "emails": unique_emails,
            "phones": unique_phones,
            "social_profiles": unique_socials,
        }
    
    async def _scrape_page(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """
        Scrape a single page using Firecrawl.
        
        Args:
            client: HTTP client
            url: Page URL
            
        Returns:
            HTML content or None if failed
        """
        if not self.is_configured():
            # Fallback to basic httpx scraping
            return await self._basic_scrape(client, url)
        
        try:
            response = await client.post(
                f"{self.base_url}/scrape",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "url": url,
                    "formats": ["html"],
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("html", "")
            else:
                # Fallback to basic scraping
                return await self._basic_scrape(client, url)
                
        except Exception:
            # Fallback to basic scraping
            return await self._basic_scrape(client, url)
    
    async def _basic_scrape(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """
        Basic scraping fallback using httpx + BeautifulSoup.
        
        Args:
            client: HTTP client
            url: Page URL
            
        Returns:
            HTML content or None if failed
        """
        try:
            # Check URL safety
            is_safe, error = is_safe_url(url)
            if not is_safe:
                return None
            
            response = await client.get(
                url,
                headers={
                    "User-Agent": settings.USER_AGENT,
                },
                follow_redirects=True,
                timeout=30,
            )
            
            if response.status_code == 200:
                return response.text
            
            return None
            
        except Exception:
            return None
