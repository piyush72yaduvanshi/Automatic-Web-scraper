"""Security headers middleware and authentication."""

import re
from urllib.parse import urlparse
from typing import Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException, Depends, Header
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def verify_api_key(x_api_key: str = Header(None)) -> bool:
    """Simple API key authentication (if AUTH_ENABLED)."""
    if not settings.AUTH_ENABLED:
        return True
    
    admin_key = getattr(settings, 'ADMIN_API_KEY', None)
    if not admin_key:
        return True
    
    if x_api_key != admin_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    
    return True


def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL to prevent SSRF attacks.
    
    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return False, "Invalid URL: no hostname"
        
        # Block localhost and loopback
        if hostname.lower() in ['localhost', '127.0.0.1', '0.0.0.0', '::1']:
            return False, "Localhost and loopback addresses are not allowed"
        
        # Block private IP ranges
        # 10.0.0.0/8
        if hostname.startswith('10.'):
            return False, "Private IP addresses are not allowed"
        
        # 172.16.0.0/12
        if hostname.startswith('172.'):
            second_octet = int(hostname.split('.')[1]) if len(hostname.split('.')) > 1 else 0
            if 16 <= second_octet <= 31:
                return False, "Private IP addresses are not allowed"
        
        # 192.168.0.0/16
        if hostname.startswith('192.168.'):
            return False, "Private IP addresses are not allowed"
        
        # Block cloud metadata endpoints
        if hostname == '169.254.169.254':
            return False, "Cloud metadata endpoints are not allowed"
        
        # Block link-local addresses
        if hostname.startswith('169.254.'):
            return False, "Link-local addresses are not allowed"
        
        return True, None
        
    except Exception as e:
        return False, f"URL parsing error: {str(e)}"


def sanitize_url(url: str) -> str:
    """
    Sanitize URL by removing potentially dangerous characters and normalizing.
    
    Args:
        url: The URL to sanitize
        
    Returns:
        Sanitized URL
    """
    # Strip whitespace
    url = url.strip()
    
    # Ensure scheme is present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Remove any null bytes or control characters
    url = re.sub(r'[\x00-\x1f\x7f]', '', url)
    
    return url


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    # Reject common placeholder domains
    placeholder_domains = ['example.com', 'test.com', 'localhost']
    domain = email.split('@')[1].lower() if '@' in email else ''
    
    if domain in placeholder_domains:
        return False
    
    return True

