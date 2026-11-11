"""Exceptions for social media lead capture."""


class SocialCaptureError(Exception):
    """Base exception for social capture errors."""
    pass


class RateLimitError(SocialCaptureError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, platform: str, retry_after: int = None, message: str = None):
        self.platform = platform
        self.retry_after = retry_after
        self.message = message or f"Rate limit exceeded for {platform}"
        super().__init__(self.message)


class AuthenticationError(SocialCaptureError):
    """Raised when authentication fails."""
    
    def __init__(self, platform: str, message: str = None):
        self.platform = platform
        self.message = message or f"Authentication failed for {platform}"
        super().__init__(self.message)


class PlatformAPIError(SocialCaptureError):
    """Raised when platform API returns an error."""
    
    def __init__(self, platform: str, status_code: int = None, message: str = None):
        self.platform = platform
        self.status_code = status_code
        self.message = message or f"API error for {platform}"
        super().__init__(self.message)
