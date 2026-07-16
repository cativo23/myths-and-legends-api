"""
Rate limiting configuration and setup.

Uses slowapi for rate limiting with configurable limits per endpoint.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

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


# Initialize limiter with default rate limit for all endpoints
limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
)


# Custom rate limit exceeded response
async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return a JSON response for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": {
                "message": f"Rate limit exceeded. {exc.detail}",
                "type": "rate_limit_exceeded",
                "retry_after": getattr(exc, "retry_after", None),
            }
        },
    )


def setup_rate_limiter(app):
    """
    Configure rate limiting on the FastAPI app.

    - All endpoints: Default limit from settings (60/min)
    - Login/password recovery: Stricter limit from settings (10/min)
    """
    app.add_middleware(SlowAPIMiddleware)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
