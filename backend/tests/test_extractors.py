"""Test data extractors."""

import pytest
from app.extractors.email import EmailExtractor
from app.extractors.phone import PhoneExtractor
from app.extractors.social import SocialExtractor


class TestEmailExtractor:
    """Test email extraction."""
    
    def test_extract_from_html(self):
        """Test email extraction from HTML."""
        html = """
        <html>
            <body>
                <p>Contact us at info@company.com</p>
                <a href="mailto:sales@company.com">Email Sales</a>
            </body>
        </html>
        """
        
        emails = EmailExtractor.extract_from_html(html, "https://test.com")
        
        assert len(emails) > 0
        assert any(e["email"] == "info@company.com" for e in emails)
        assert any(e["email"] == "sales@company.com" for e in emails)
    
    def test_exclude_placeholders(self):
        """Test that placeholders are excluded."""
        html = "<p>Contact: example@example.com</p>"
        
        emails = EmailExtractor.extract_from_html(html, "https://test.com")
        
        assert len(emails) == 0


class TestPhoneExtractor:
    """Test phone extraction."""
    
    def test_extract_indian_phone(self):
        """Test Indian phone number extraction."""
        text = "Call us at +91 9876543210 or 9876543210"
        
        phones = PhoneExtractor.extract_from_text(text, "https://test.com", "IN")
        
        assert len(phones) > 0
        assert any(p["normalized"] == "+919876543210" for p in phones)
    
    def test_normalize_phone(self):
        """Test phone normalization."""
        phone = PhoneExtractor.normalize_phone("+91 98765 43210", "IN")
        
        assert phone == "+919876543210"


class TestSocialExtractor:
    """Test social profile extraction."""
    
    def test_extract_instagram(self):
        """Test Instagram URL extraction."""
        html = '<a href="https://www.instagram.com/company_name/">Instagram</a>'
        
        socials = SocialExtractor.extract_from_html(html, "https://test.com")
        
        instagram = [s for s in socials if s["platform"] == "INSTAGRAM"]
        assert len(instagram) > 0
    
    def test_extract_linkedin(self):
        """Test LinkedIn URL extraction."""
        html = '<a href="https://www.linkedin.com/company/test-company/">LinkedIn</a>'
        
        socials = SocialExtractor.extract_from_html(html, "https://test.com")
        
        linkedin = [s for s in socials if s["platform"] == "LINKEDIN"]
        assert len(linkedin) > 0
    
    def test_normalize_twitter_to_x(self):
        """Test Twitter URL normalization to X."""
        url = "https://twitter.com/company"
        
        normalized = SocialExtractor.normalize_url(url, "X")
        
        assert "x.com" in normalized
