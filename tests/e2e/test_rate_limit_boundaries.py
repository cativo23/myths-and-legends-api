"""
E2E rate-limit boundaries for the endpoints not covered elsewhere. Login (auth
limit) and a read endpoint (default limit) are tested in tests/domains/test_auth.py
and tests/test_cache_reference_reads.py.

Each test uses a single limited endpoint and requests that fail cheaply (unknown
email, invalid token, no credentials): the limiter counts the request whatever
its outcome. Limiter state is cleared before every test by the autouse
`_reset_rate_limiter` fixture in tests/conftest.py, so exhausting a budget here
cannot leak into another test.
"""
from fastapi.testclient import TestClient

from app.core.config import settings


def _statuses_up_to_limit(send, limit: int) -> list[int]:
    return [send().status_code for _ in range(limit)]


def _assert_429_with_json_body(response) -> None:
    assert response.status_code == 429
    assert isinstance(response.json(), dict)  # .json() raising is the real check


def _assert_429_with_error_envelope(response) -> None:
    """Per-route limits go through the app's handler and use the `detail` envelope."""
    _assert_429_with_json_body(response)
    assert response.json()["detail"]["type"] == "rate_limit_exceeded"


# NOTE: the default limit is enforced by SlowAPIMiddleware, which bypasses the
# app's handler, so its 429 body is {"error": "..."} instead of the `detail`
# envelope. Pinned here as current behavior only (JSON, no exact shape); see
# docs/ROADMAP.md session 1.6 for the pending decision.


def test_should_return_429_on_password_recovery_after_the_auth_limit(
    client: TestClient,
):
    limit = settings.RATE_LIMIT_AUTH_PER_MINUTE

    def send():
        return client.post("/api/v1/auth/password-recovery/nobody@example.com")

    assert _statuses_up_to_limit(send, limit) == [200] * limit
    _assert_429_with_error_envelope(send())


def test_should_return_429_on_password_reset_after_the_auth_limit(client: TestClient):
    limit = settings.RATE_LIMIT_AUTH_PER_MINUTE

    def send():
        return client.post(
            "/api/v1/auth/reset-password/",
            json={"token": "not-a-valid-token", "new_password": "irrelevant-pass-1"},
        )

    assert _statuses_up_to_limit(send, limit) == [400] * limit
    _assert_429_with_error_envelope(send())


def test_should_return_429_on_refresh_after_the_default_limit(client: TestClient):
    limit = settings.RATE_LIMIT_PER_MINUTE

    def send():
        return client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-valid-token"}
        )

    assert _statuses_up_to_limit(send, limit) == [401] * limit
    _assert_429_with_json_body(send())


def test_should_return_429_on_logout_after_the_default_limit(client: TestClient):
    limit = settings.RATE_LIMIT_PER_MINUTE

    def send():
        return client.post("/api/v1/auth/logout")

    assert _statuses_up_to_limit(send, limit) == [401] * limit
    _assert_429_with_json_body(send())
