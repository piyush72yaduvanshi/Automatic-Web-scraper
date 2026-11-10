"""Rate limiting using Redis backend."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Create limiter with Redis storage for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=str(settings.REDIS_URL),
    strategy="fixed-window",
)
