"""
Tests for middleware ordering (request_id + structured logging).

Regression test for a bug where RequestIDMiddleware and LoggingMiddleware
were registered in the wrong order in app/main.py. Starlette's
add_middleware() prepends to the middleware stack, so the LAST middleware
registered ends up OUTERMOST and runs FIRST on the way in. With the buggy
order, LoggingMiddleware read request.state.request_id before
RequestIDMiddleware had set it, so every structured log line had
request_id="unknown".
"""

import logging

from fastapi.testclient import TestClient


class TestRequestIdLoggingOrder:
    """Verify RequestIDMiddleware runs before LoggingMiddleware."""

    def test_response_has_request_id_header(self, client: TestClient):
        """The X-Request-ID response header should always be present and non-empty."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        request_id = response.headers.get("X-Request-ID")
        assert request_id
        assert len(request_id) > 0

    def test_logged_request_id_matches_response_header(
        self, client: TestClient, caplog
    ):
        """
        The request_id captured in the structured log for a request must match
        the X-Request-ID returned in that same request's response header.

        If middleware ordering regresses (Logging registered after RequestID,
        i.e. Logging ends up innermost/reads state first), this fails because
        the log record's request_id falls back to "unknown" while the response
        header still carries a real UUID.
        """
        with caplog.at_level(logging.INFO, logger="api.requests"):
            response = client.get("/api/v1/health")

        assert response.status_code == 200
        response_request_id = response.headers.get("X-Request-ID")
        assert response_request_id

        matching_records = [
            record
            for record in caplog.records
            if record.name == "api.requests"
            and getattr(record, "path", None) == "/api/v1/health"
        ]
        assert matching_records, "expected LoggingMiddleware to emit a log record"

        logged_request_id = getattr(matching_records[-1], "request_id", None)
        assert logged_request_id is not None
        assert logged_request_id != "unknown"
        assert logged_request_id == response_request_id
