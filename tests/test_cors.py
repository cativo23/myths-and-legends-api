"""
Tests for CORS middleware behavior (app.main's CORSMiddleware configuration).

Regression coverage for a bug where the CORS setup did `.replace("/", "")` on
every configured origin, silently mangling e.g. "https://example.com" into
"https:example.com" so it would never match a real browser Origin header.
"""

from fastapi.testclient import TestClient

from app.core.config import settings


class TestCorsMiddleware:
    """Integration tests for CORS origin-handling behavior."""

    def test_allowed_origin_is_echoed_back_unmangled(self, client: TestClient):
        """A request with an Origin header matching a configured allowed
        origin should get that exact origin back in
        access-control-allow-origin — not a mangled version like
        'http:localhost:3000'."""
        origin = settings.BACKEND_CORS_ORIGINS[0]
        assert origin == "http://localhost:3000"

        response = client.get("/", headers={"Origin": origin})

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
