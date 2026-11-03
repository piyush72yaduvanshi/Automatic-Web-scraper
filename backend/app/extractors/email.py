"""Email extraction utilities."""

import re
from typing import List, Set
from urllib.parse import urlparse, unquote

from app.core.security import validate_email


class EmailExtractor:
    """Extract and validate email addresses from HTML content."""
    
    # Common placeholders to exclude
    PLACEHOLDERS = {
        "example@example.com",
        "test@test.com",
        "email@example.com",
        "your@email.com",
        "info@example.com",
        "contact@example.com",
        "user@domain.com",
    }
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    )
    
    @staticmethod
    def decode_cloudflare_email(cf_hex: str) -> str:
        """Decode Cloudflare obfuscated email XOR cipher."""
        try:
            r = int(cf_hex[:2], 16)
            email = ''.join(chr(int(cf_hex[i:i+2], 16) ^ r) for i in range(2, len(cf_hex), 2))
            return email.lower().strip()
        except Exception:
            return ""

    @classmethod
    def extract_from_html(cls, html: str, source_url: str) -> List[dict]:
        """
        Extract emails from HTML content with Cloudflare and anti-obfuscation decoding.
        
        Args:
            html: HTML content
            source_url: Source URL for attribution
            
        Returns:
            List of extracted email dictionaries
        """
        emails: Set[str] = set()

        # 1. Decode Cloudflare protected emails (data-cfemail)
        cf_pattern = re.compile(r'data-cfemail=["\']([a-f0-9]+)["\']', re.IGNORECASE)
        for match in cf_pattern.finditer(html):
            decoded = cls.decode_cloudflare_email(match.group(1))
            if decoded and "@" in decoded:
                emails.add(decoded)

        # 2. Extract from mailto: links
        mailto_pattern = re.compile(r'mailto:([^?"\'<>\s]+)', re.IGNORECASE)
        for match in mailto_pattern.finditer(html):
            email = unquote(match.group(1)).strip()
            if email:
                emails.add(email.lower())

        # 3. Handle HTML entity and obfuscated forms
        clean_html = html.replace('&#64;', '@').replace('&#x40;', '@').replace('&commat;', '@')
        
        # 4. Extract visible email addresses
        for match in cls.EMAIL_PATTERN.finditer(clean_html):
            email = match.group(0).strip().lower()
            if email:
                emails.add(email)

        # 5. Extract obfuscated [at] [dot] patterns
        obf_pattern = re.compile(r'\b([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\s+at\s+)\s*([A-Za-z0-9.-]+)\s*(?:\[dot\]|\(dot\)|\s+dot\s+)\s*([A-Za-z]{2,})\b', re.IGNORECASE)
        for match in obf_pattern.finditer(clean_html):
            constructed = f"{match.group(1)}@{match.group(2)}.{match.group(3)}".lower()
            emails.add(constructed)
        
        # Filter and validate
        results = []
        for email in emails:
            # Skip placeholders
            if email in cls.PLACEHOLDERS:
                continue
            
            # Validate email format
            if not validate_email(email):
                continue
            
            # Skip image files (.jpg, .png, etc. in email-like patterns)
            if any(ext in email for ext in ['.jpg@', '.png@', '.gif@', '.jpeg@']):
                continue
            
            results.append({
                "email": email,
                "source_url": source_url,
                "verification_status": "unverified"
            })
        
        return results
    
    @classmethod
    def extract_from_text(cls, text: str, source_url: str) -> List[dict]:
        """
        Extract emails from plain text.
        
        Args:
            text: Plain text content
            source_url: Source URL for attribution
            
        Returns:
            List of extracted email dictionaries
        """
        emails: Set[str] = set()
        
        # Extract all email patterns
        for match in cls.EMAIL_PATTERN.finditer(text):
            email = match.group(0).strip().lower()
            if email and email not in cls.PLACEHOLDERS:
                if validate_email(email):
                    emails.add(email)
        
        results = []
        for email in emails:
            results.append({
                "email": email,
                "source_url": source_url,
                "verification_status": "unverified"
            })
        
        return results
    
    @classmethod
    def deduplicate(cls, emails: List[dict]) -> List[dict]:
        """
        Remove duplicate emails, keeping the first occurrence.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for email_dict in emails:
            email = email_dict.get("email", "").lower()
            if email and email not in seen:
                seen.add(email)
                unique.append(email_dict)
        
        return unique
