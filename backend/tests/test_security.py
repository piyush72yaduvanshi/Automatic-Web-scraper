"""Test security utilities."""

from app.core.security import is_safe_url, validate_email


class TestSSRFProtection:
    """Test SSRF protection."""
    
    def test_safe_url(self):
        """Test that safe URLs are allowed."""
        is_safe, error = is_safe_url("https://example.com/contact")
        assert is_safe is True
        assert error is None
    
    def test_block_localhost(self):
        """Test that localhost is blocked."""
        is_safe, error = is_safe_url("http://localhost/api")
        assert is_safe is False
        assert "localhost" in error.lower()
    
    def test_block_private_ip(self):
        """Test that private IPs are blocked."""
        is_safe, error = is_safe_url("http://192.168.1.1/")
        assert is_safe is False
    
    def test_block_metadata_endpoint(self):
        """Test that cloud metadata endpoints are blocked."""
        is_safe, error = is_safe_url("http://169.254.169.254/")
        assert is_safe is False


class TestEmailValidation:
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid email."""
        assert validate_email("test@company.com") is True
    
    def test_invalid_email(self):
        """Test invalid email."""
        assert validate_email("not-an-email") is False
    
    def test_placeholder_email(self):
        """Test placeholder email is rejected."""
        assert validate_email("test@example.com") is False
