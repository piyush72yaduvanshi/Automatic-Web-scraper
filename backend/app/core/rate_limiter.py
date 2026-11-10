"""Rate limiting using in-memory storage (Redis backend temporarily disabled)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter with in-memory storage for local development
# Note: Redis backend temporarily disabled due to authentication issues
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    strategy="fixed-window",
)
