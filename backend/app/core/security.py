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
        import ipaddress
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            return False, "Invalid URL: no hostname"
        
        # Block localhost names
        if hostname.lower() in ['localhost', '0.0.0.0', '::1']:
            return False, "Localhost and loopback addresses are not allowed"
        
        # Check IP address properties if hostname is an IP
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_loopback:
                return False, "Localhost and loopback addresses are not allowed"
            if ip.is_private:
                return False, "Private IP addresses are not allowed"
            if ip.is_link_local:
                return False, "Link-local and cloud metadata endpoints are not allowed"
            if ip.is_reserved or ip.is_unspecified:
                return False, "Reserved IP addresses are not allowed"
        except ValueError:
            # It's a domain name (not raw IP)
            pass
        
        # Fallback string checks for non-resolved prefixes
        if hostname.startswith('127.'):
            return False, "Localhost and loopback addresses are not allowed"
        if hostname.startswith('10.') or hostname.startswith('192.168.'):
            return False, "Private IP addresses are not allowed"
        if hostname.startswith('169.254.'):
            return False, "Cloud metadata endpoints are not allowed"
        
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

