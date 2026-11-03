"""Social profile URL extraction utilities."""

import re
from typing import List, Set, Optional
from urllib.parse import urlparse, unquote


class SocialExtractor:
    """Extract and normalize social media profile URLs."""
    
    # Social media URL patterns
    PATTERNS = {
        "INSTAGRAM": [
            re.compile(r'https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)/?', re.IGNORECASE),
            re.compile(r'instagram\.com/([a-zA-Z0-9_.]+)', re.IGNORECASE),
        ],
        "LINKEDIN": [
            re.compile(r'https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9\-]+)/?', re.IGNORECASE),
            re.compile(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-]+)/?', re.IGNORECASE),
            re.compile(r'linkedin\.com/company/([a-zA-Z0-9\-]+)', re.IGNORECASE),
        ],
        "FACEBOOK": [
            re.compile(r'https?://(?:www\.)?facebook\.com/([a-zA-Z0-9.]+)/?', re.IGNORECASE),
            re.compile(r'https?://(?:www\.)?fb\.com/([a-zA-Z0-9.]+)/?', re.IGNORECASE),
            re.compile(r'facebook\.com/([a-zA-Z0-9.]+)', re.IGNORECASE),
        ],
        "X": [
            re.compile(r'https?://(?:www\.)?(?:twitter|x)\.com/([a-zA-Z0-9_]+)/?', re.IGNORECASE),
            re.compile(r'(?:twitter|x)\.com/([a-zA-Z0-9_]+)', re.IGNORECASE),
        ],
    }
    
    # Paths to exclude (personal profiles, pages, etc.)
    EXCLUDE_PATHS = {
        "profile.php",
        "pages",
        "people",
        "hashtag",
        "search",
        "explore",
        "share",
    }
    
    @classmethod
    def extract_from_html(cls, html: str, source_url: str) -> List[dict]:
        """
        Extract social media URLs from HTML content.
        
        Args:
            html: HTML content
            source_url: Source URL for attribution
            
        Returns:
            List of extracted social profile dictionaries
        """
        results = []
        
        for platform, patterns in cls.PATTERNS.items():
            urls = cls._extract_platform_urls(html, patterns, platform)
            
            for url in urls:
                # Validate and normalize
                normalized = cls.normalize_url(url, platform)
                if normalized and cls._is_valid_profile(normalized, platform):
                    results.append({
                        "platform": platform,
                        "url": normalized,
                        "source_url": source_url,
                        "verification_status": "unverified"
                    })
        
        return results
    
    @classmethod
    def _extract_platform_urls(cls, html: str, patterns: List[re.Pattern], platform: str) -> Set[str]:
        """Extract URLs for a specific platform."""
        urls: Set[str] = set()
        
        for pattern in patterns:
            for match in pattern.finditer(html):
                url = match.group(0)
                # Clean and decode
                url = unquote(url).strip()
                urls.add(url)
        
        return urls
    
    @classmethod
    def normalize_url(cls, url: str, platform: str) -> Optional[str]:
        """
        Normalize social media URL.
        
        Args:
            url: Social media URL
            platform: Platform name
            
        Returns:
            Normalized URL or None if invalid
        """
        try:
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            
            # Extract username/handle
            path = parsed.path.strip('/')
            
            # Remove query parameters and fragments
            if platform == "INSTAGRAM":
                if path:
                    return f"https://www.instagram.com/{path.split('/')[0]}/"
            
            elif platform == "LINKEDIN":
                full_path = parsed.path.lower()
                if '/company/' in full_path or full_path.startswith('/company'):
                    parts = [p for p in parsed.path.split('/') if p and p.lower() != 'company']
                    if parts:
                        return f"https://www.linkedin.com/company/{parts[0]}/"
                elif '/in/' in full_path or full_path.startswith('/in'):
                    parts = [p for p in parsed.path.split('/') if p and p.lower() != 'in']
                    if parts:
                        return f"https://www.linkedin.com/in/{parts[0]}/"
            
            elif platform == "FACEBOOK":
                if path and not any(excl in path for excl in cls.EXCLUDE_PATHS):
                    return f"https://www.facebook.com/{path.split('/')[0]}/"
            
            elif platform == "X":
                if path:
                    # Normalize twitter.com to x.com
                    handle = path.split('/')[0]
                    return f"https://www.x.com/{handle}/"
            
            return None
            
        except Exception:
            return None
    
    @classmethod
    def _is_valid_profile(cls, url: str, platform: str) -> bool:
        """
        Validate if URL is a valid business profile.
        
        Args:
            url: Normalized URL
            platform: Platform name
            
        Returns:
            True if valid business profile
        """
        # Exclude common non-business paths
        exclude_keywords = [
            'home', 'login', 'signup', 'settings', 'privacy',
            'terms', 'help', 'support', 'about', 'explore'
        ]
        
        url_lower = url.lower()
        for keyword in exclude_keywords:
            if f'/{keyword}' in url_lower:
                return False
        
        return True
    
    @classmethod
    def deduplicate(cls, profiles: List[dict]) -> List[dict]:
        """
        Remove duplicate social profiles.
        
        Args:
            profiles: List of social profile dictionaries
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for profile in profiles:
            key = (profile.get("platform"), profile.get("url", "").lower())
            if key not in seen and key[1]:
                seen.add(key)
                unique.append(profile)
        
        return unique
