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

    Only honors X-Forwarded-For when the directly connecting peer is a
    trusted proxy (settings.TRUSTED_PROXY_IPS); otherwise any client could
    set an arbitrary value and get a fresh rate-limit bucket per request,
    bypassing brute-force protection entirely. Falls back to the real
    connecting IP address (via slowapi's get_remote_address) by default.
    """
    client_host = request.client.host if request.client else None
    if client_host and client_host in settings.TRUSTED_PROXY_IPS:
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
    - Login/password recovery/refresh: additionally decorated with a
      stricter per-route limit from settings (10/min)

    A route-level @limiter.limit(...) decorator does NOT replace the
    default limit above — slowapi enforces both, additively. A decorated
    route is rejected once either limit is hit, whichever comes first;
    it does not get a separate 10/min budget in place of the 60/min default.
    """
    app.add_middleware(SlowAPIMiddleware)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
