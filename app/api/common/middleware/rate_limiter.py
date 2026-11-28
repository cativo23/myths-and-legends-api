"""
Rate limiting configuration and setup.

Uses slowapi for rate limiting with configurable limits per endpoint.
"""

import math
import time

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


def _seconds_until_reset(request: Request) -> int | None:
    """Seconds until the window of the limit that was just hit resets.

    RateLimitExceeded carries no retry time, so it is read from the limiter's
    window stats. A 429 must never turn into a 500, hence the broad except:
    on any failure the client simply gets `None`.
    """
    try:
        item, key_parts = request.state.view_rate_limit
        reset_at = limiter.limiter.get_window_stats(item, *key_parts)[0]
        return max(1, math.ceil(reset_at - time.time()))
    except Exception:
        return None


# Custom rate limit exceeded response.
# Must stay a plain `def`: SlowAPIMiddleware (which enforces the default limit)
# swaps any coroutine handler for slowapi's own `{"error": ...}` one, so an
# `async def` here would only apply to per-route limits.
def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return a JSON response for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": {
                "message": f"Rate limit exceeded. {exc.detail}",
                "type": "rate_limit_exceeded",
                "retry_after": _seconds_until_reset(request),
            }
        },
    )


def setup_rate_limiter(app):
    """
    Configure rate limiting on the FastAPI app.

    - All endpoints: Default limit from settings (60/min)
    - Login/password recovery/reset: additionally decorated with a
      stricter per-route limit from settings (10/min), since these accept
      a guessable secret (password or recovery token) and are brute-force
      targets
    - /auth/refresh and /auth/logout are deliberately left at just the
      default limit: both require already possessing a valid, unguessable
      token, so the stricter brute-force limit doesn't apply the same way

    A route-level @limiter.limit(...) decorator does NOT replace the
    default limit above — slowapi enforces both, additively. A decorated
    route is rejected once either limit is hit, whichever comes first;
    it does not get a separate 10/min budget in place of the 60/min default.
    """
    app.add_middleware(SlowAPIMiddleware)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
