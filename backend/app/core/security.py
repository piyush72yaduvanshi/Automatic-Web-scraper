"""Security utilities for URL validation and SSRF protection."""

import re
import ipaddress
from urllib.parse import urlparse
from typing import Optional

from app.core.config import settings


def is_safe_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL for SSRF protection.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            return False, f"Invalid scheme: {parsed.scheme}. Only http and https are allowed."
        
        # Check hostname
        if not parsed.hostname:
            return False, "Missing hostname in URL"
        
        hostname = parsed.hostname.lower()
        
        # Check blocked domains
        for blocked in settings.BLOCKED_DOMAINS:
            if hostname == blocked or hostname.endswith(f".{blocked}"):
                return False, f"Blocked domain: {hostname}"
        
        # Check for private IP addresses (if not allowed)
        if not settings.ALLOW_PRIVATE_IPS:
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False, f"Private IP address not allowed: {hostname}"
            except ValueError:
                # Not an IP address, continue with hostname checks
                pass
        
        # Check for localhost variants
        localhost_patterns = [
            "localhost",
            "127.",
            "0.0.0.0",
            "[::",
            "0:0:0:0:0:0:0:1",
        ]
        for pattern in localhost_patterns:
            if pattern in hostname:
                return False, f"Localhost access not allowed: {hostname}"
        
        # Check for cloud metadata endpoints
        metadata_endpoints = [
            "169.254.169.254",  # AWS, Azure, GCP
            "metadata.google.internal",  # GCP
            "169.254.169.253",  # Azure
        ]
        for endpoint in metadata_endpoints:
            if endpoint in hostname:
                return False, f"Cloud metadata endpoint not allowed: {hostname}"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def sanitize_url(url: str) -> str:
    """
    Sanitize URL by removing dangerous components.
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL
    """
    # Remove any null bytes
    url = url.replace("\x00", "")
    
    # Strip whitespace
    url = url.strip()
    
    return url


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Check pattern
    if not re.match(pattern, email):
        return False
    
    # Exclude common placeholders
    placeholders = [
        "example.com",
        "test.com",
        "sample.com",
        "domain.com",
        "email.com",
        "noreply",
        "no-reply",
    ]
    
    email_lower = email.lower()
    for placeholder in placeholders:
        if placeholder in email_lower:
            return False
    
    return True


def normalize_phone_number(phone: str, region: str = "IN") -> Optional[str]:
    """
    Normalize phone number using phonenumbers library.
    
    Args:
        phone: Phone number to normalize
        region: Default region code (default: IN for India)
        
    Returns:
        Normalized phone number in E164 format or None if invalid
    """
    try:
        import phonenumbers
        
        # Parse phone number
        parsed = phonenumbers.parse(phone, region)
        
        # Validate
        if not phonenumbers.is_valid_number(parsed):
            return None
        
        # Return E164 format
        return phonenumbers.format_number(
            parsed, 
            phonenumbers.PhoneNumberFormat.E164
        )
        
    except Exception:
        return None


import hmac
import hashlib
import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


def verify_api_key(
    api_key_header_val: Optional[str] = Security(api_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(http_bearer)
) -> bool:
    """
    Authenticate requests using X-API-Key header or Bearer token.
    If AUTH_ENABLED is False (development/testing default), allows request through.
    """
    if not settings.AUTH_ENABLED:
        return True

    provided_key = None
    if api_key_header_val:
        provided_key = api_key_header_val
    elif bearer_creds:
        provided_key = bearer_creds.credentials

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided. Pass 'X-API-Key' or 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Constant time comparison to prevent timing attacks
    expected_key = settings.ADMIN_API_KEY.encode("utf-8")
    actual_key = provided_key.encode("utf-8")

    if not hmac.compare_digest(expected_key, actual_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials.",
        )

    return True


def hash_secret(secret: str) -> str:
    """Hash a secret/password with salt using SHA-256."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + secret).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"


def verify_secret(secret: str, stored_hash: str) -> bool:
    """Verify secret against stored salt$hash."""
    try:
        salt, expected_hash = stored_hash.split("$", 1)
        actual_hash = hashlib.sha256((salt + secret).encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected_hash, actual_hash)
    except Exception:
        return False

