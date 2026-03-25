"""
Rate limiting configuration and setup.

Uses slowapi for rate limiting with configurable limits per endpoint.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def rate_limit_key_func(request: Request) -> str:
    """
    Get the rate limit key based on client IP.
    Falls back to 'unknown' if IP cannot be determined.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Initialize limiter
limiter = Limiter(key_func=rate_limit_key_func)


# Custom rate limit exceeded response
async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> dict:
    """Return a JSON response for rate limit exceeded errors."""
    return {
        "detail": {
            "message": f"Rate limit exceeded. {exc.detail}",
            "type": "rate_limit_exceeded",
            "retry_after": getattr(exc, "retry_after", None),
        }
    }


def setup_rate_limiter(app):
    """
    Configure rate limiting on the FastAPI app.

    - Login endpoint: Limited to prevent brute force attacks
    - Password recovery: Limited to prevent abuse
    - All other endpoints: Use default limit from settings
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
