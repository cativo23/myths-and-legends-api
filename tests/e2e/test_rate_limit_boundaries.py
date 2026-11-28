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


def _assert_429_envelope(response) -> None:
    """Every limit, per-route or default, answers the same `detail` envelope."""
    assert response.status_code == 429
    body = response.json()
    assert set(body) == {"detail"}
    assert set(body["detail"]) == {"message", "type", "retry_after"}
    assert body["detail"]["type"] == "rate_limit_exceeded"


def test_should_return_429_on_password_recovery_after_the_auth_limit(
    client: TestClient,
):
    limit = settings.RATE_LIMIT_AUTH_PER_MINUTE

    def send():
        return client.post("/api/v1/auth/password-recovery/nobody@example.com")

    assert _statuses_up_to_limit(send, limit) == [200] * limit
    _assert_429_envelope(send())


def test_should_return_429_on_password_reset_after_the_auth_limit(client: TestClient):
    limit = settings.RATE_LIMIT_AUTH_PER_MINUTE

    def send():
        return client.post(
            "/api/v1/auth/reset-password/",
            json={"token": "not-a-valid-token", "new_password": "irrelevant-pass-1"},
        )

    assert _statuses_up_to_limit(send, limit) == [400] * limit
    _assert_429_envelope(send())


def test_should_return_429_on_refresh_after_the_default_limit(client: TestClient):
    limit = settings.RATE_LIMIT_PER_MINUTE

    def send():
        return client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-valid-token"}
        )

    assert _statuses_up_to_limit(send, limit) == [401] * limit
    _assert_429_envelope(send())


def test_should_return_429_on_logout_after_the_default_limit(client: TestClient):
    limit = settings.RATE_LIMIT_PER_MINUTE

    def send():
        return client.post("/api/v1/auth/logout")

    assert _statuses_up_to_limit(send, limit) == [401] * limit
    _assert_429_envelope(send())


def _assert_retry_after_is_seconds_to_wait(response) -> None:
    retry_after = response.json()["detail"]["retry_after"]
    assert isinstance(retry_after, int)
    assert 1 <= retry_after <= 60  # both windows are one minute long


def test_should_tell_how_long_to_wait_when_the_auth_limit_is_hit(client: TestClient):
    for _ in range(settings.RATE_LIMIT_AUTH_PER_MINUTE):
        client.post("/api/v1/auth/password-recovery/nobody@example.com")

    _assert_retry_after_is_seconds_to_wait(
        client.post("/api/v1/auth/password-recovery/nobody@example.com")
    )


def test_should_tell_how_long_to_wait_when_the_default_limit_is_hit(
    client: TestClient,
):
    for _ in range(settings.RATE_LIMIT_PER_MINUTE):
        client.post("/api/v1/auth/logout")

    _assert_retry_after_is_seconds_to_wait(client.post("/api/v1/auth/logout"))
