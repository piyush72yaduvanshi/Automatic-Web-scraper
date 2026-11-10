"""Security headers middleware and authentication."""

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
