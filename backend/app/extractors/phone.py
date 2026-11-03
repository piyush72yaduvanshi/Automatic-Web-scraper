"""Phone number extraction utilities."""

import re
from typing import List, Set, Optional

import phonenumbers
from phonenumbers import NumberParseException


class PhoneExtractor:
    """Extract and normalize phone numbers from HTML content."""
    
    # Phone number patterns for different formats
    PHONE_PATTERNS = [
        # Indian format: +91 9876543210, +91-9876543210, +919876543210
        re.compile(r'\+91[-\s]?\d{10}'),
        # Indian format without country code: 9876543210, 98765 43210
        re.compile(r'\b[6-9]\d{9}\b'),
        # With parentheses: (123) 456-7890
        re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
        # International format: +1-234-567-8900
        re.compile(r'\+\d{1,3}[-.\s]?\d{1,14}'),
        # tel: links
        re.compile(r'tel:([+\d\s\-\(\)]+)', re.IGNORECASE),
    ]
    
    @classmethod
    def extract_from_html(cls, html: str, source_url: str, default_region: str = "IN") -> List[dict]:
        """
        Extract phone numbers from HTML content.
        
        Args:
            html: HTML content
            source_url: Source URL for attribution
            default_region: Default region code for parsing (default: IN for India)
            
        Returns:
            List of extracted phone dictionaries
        """
        phones: Set[str] = set()
        
        # Extract from tel: links
        tel_pattern = re.compile(r'tel:([+\d\s\-\(\)]+)', re.IGNORECASE)
        for match in tel_pattern.finditer(html):
            phone = match.group(1).strip()
            if phone:
                phones.add(phone)

        # Extract from WhatsApp links (wa.me and api.whatsapp.com)
        wa_pattern = re.compile(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?\d+)', re.IGNORECASE)
        for match in wa_pattern.finditer(html):
            wa_num = match.group(1).strip()
            if wa_num:
                phones.add(wa_num)
        
        # Extract from all patterns
        for pattern in cls.PHONE_PATTERNS:
            for match in pattern.finditer(html):
                phone = match.group(0).strip()
                # Clean tel: prefix
                phone = phone.replace('tel:', '')
                if phone:
                    phones.add(phone)
        
        # Normalize and validate
        results = []
        for phone in phones:
            normalized = cls.normalize_phone(phone, default_region)
            if normalized:
                results.append({
                    "original": phone,
                    "normalized": normalized,
                    "source_url": source_url,
                    "verification_status": "unverified"
                })
        
        return results
    
    @classmethod
    def extract_from_text(cls, text: str, source_url: str, default_region: str = "IN") -> List[dict]:
        """
        Extract phone numbers from plain text.
        
        Args:
            text: Plain text content
            source_url: Source URL for attribution
            default_region: Default region code
            
        Returns:
            List of extracted phone dictionaries
        """
        phones: Set[str] = set()
        
        # Extract from all patterns
        for pattern in cls.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                phone = match.group(0).strip()
                if phone:
                    phones.add(phone)
        
        results = []
        for phone in phones:
            normalized = cls.normalize_phone(phone, default_region)
            if normalized:
                results.append({
                    "original": phone,
                    "normalized": normalized,
                    "source_url": source_url,
                    "verification_status": "unverified"
                })
        
        return results
    
    @classmethod
    def normalize_phone(cls, phone: str, region: str = "IN") -> Optional[str]:
        """
        Normalize phone number to E164 format.
        
        Args:
            phone: Phone number string
            region: Default region code
            
        Returns:
            Normalized phone number or None if invalid
        """
        try:
            # Clean the phone number
            phone = phone.strip()
            
            # Parse the phone number
            parsed = phonenumbers.parse(phone, region)
            
            # Validate
            if not phonenumbers.is_valid_number(parsed):
                return None
            
            # Return E164 format
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
            
        except NumberParseException:
            return None
    
    @classmethod
    def deduplicate(cls, phones: List[dict]) -> List[dict]:
        """
        Remove duplicate phone numbers based on normalized value.
        
        Args:
            phones: List of phone dictionaries
            
        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []
        
        for phone_dict in phones:
            normalized = phone_dict.get("normalized", "")
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(phone_dict)
        
        return unique
