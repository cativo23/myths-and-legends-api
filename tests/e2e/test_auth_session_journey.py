"""
E2E journey: one user's session from login to logout. Malformed, expired and
wrong-type tokens, and each endpoint's own error cases, are covered in
tests/domains/test_auth.py and are not repeated here.
"""
from fastapi.testclient import TestClient


def _login(client: TestClient, user: dict) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )
    assert response.status_code == 200
    return response.json()


def _refresh(client: TestClient, refresh_token: str):
    return client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})


def _me(client: TestClient, access_token: str):
    return client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )


def test_should_keep_a_session_alive_across_refreshes_until_logout(
    client: TestClient, test_user: dict
):
    session = _login(client, test_user)
    assert _me(client, session["access_token"]).json()["email"] == test_user["email"]

    first = _refresh(client, session["refresh_token"])
    assert first.status_code == 200
    assert _me(client, first.json()["access_token"]).status_code == 200

    second = _refresh(client, first.json()["refresh_token"])
    assert second.status_code == 200
    assert _me(client, second.json()["access_token"]).status_code == 200

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {second.json()['access_token']}"},
    )
    assert logout.status_code == 200
    assert _refresh(client, second.json()["refresh_token"]).status_code == 401


def test_should_reject_a_reused_refresh_token_without_revoking_the_newer_session(
    client: TestClient, test_user: dict
):
    session = _login(client, test_user)
    rotated = _refresh(client, session["refresh_token"])
    assert rotated.status_code == 200

    # The 401 itself is pinned in tests/domains/test_auth.py; here it is the
    # precondition for the assertion below, which is the new behavior.
    reused = _refresh(client, session["refresh_token"])
    assert reused.status_code == 401

    # The failed reuse must not have touched the stored token of the newer session.
    assert _refresh(client, rotated.json()["refresh_token"]).status_code == 200


def test_should_allow_only_one_active_session_per_user(
    client: TestClient, test_user: dict
):
    first_session = _login(client, test_user)
    second_session = _login(client, test_user)
    assert first_session["refresh_token"] != second_session["refresh_token"]

    assert _refresh(client, first_session["refresh_token"]).status_code == 401
    assert _refresh(client, second_session["refresh_token"]).status_code == 200
