"""
Tests for Auth domain.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.domains.users.models.user import User
from app.api.v1.domains.users.services.user import user as user_service
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import generate_password_reset_token, verify_password_reset_token


class TestAuthEndpoints:
    """Integration tests for Auth endpoints."""

    def test_login_success(self, client: TestClient, test_user: dict):
        """Test successful login returns access_token, expires_at, token_type."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "expires_at" in data
        assert "token_type" in data
        assert data["token_type"] == "Bearer"
        assert data["access_token"]

    def test_login_wrong_password(self, client: TestClient, test_user: dict):
        """Test login with wrong password returns 400."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user["email"],
                "password": "wrongpassword123",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "Incorrect email or password" in data["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email returns 400."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword123",
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "Incorrect email or password" in data["detail"]

    def test_login_inactive_user(self, client: TestClient, db: Session):
        """Test login with inactive user returns 400."""
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False,
        )
        db.add(inactive_user)
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "inactive@example.com", "password": "password123"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "Inactive user" in data["detail"]

    def test_get_current_user(self, client: TestClient, auth_headers: dict):
        """Test getting current user with valid token returns user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "id" in data

    def test_get_current_user_superuser(self, client: TestClient, superuser_headers: dict):
        """Test getting current superuser returns superuser info."""
        response = client.get("/api/v1/auth/me", headers=superuser_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@example.com"
        assert data["is_superuser"] is True

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without token returns 401."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token returns 403."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"},
        )
        assert response.status_code == 403

    def test_protected_endpoint_rejects_refresh_token(
        self, client: TestClient, test_user: dict
    ):
        """Test that a refresh token can't be used as a Bearer access token
        against a protected endpoint (type-confusion guard)."""
        from app.core import security

        refresh_token = security.create_refresh_token(test_user["id"])

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == 403

    def test_password_recovery_existing_user(self, client: TestClient, test_user: dict):
        """Test password recovery for existing user sends email."""
        with patch("app.api.v1.domains.auth.endpoints.auth.send_reset_password_email") as mock_send:
            response = client.post(
                f"/api/v1/auth/password-recovery/{test_user['email']}"
            )
            assert response.status_code == 200
            data = response.json()
            assert "password recovery email has been sent" in data["msg"]
            mock_send.assert_called_once()

    def test_password_recovery_user_not_found(self, client: TestClient):
        """Test password recovery for non-existent user returns a generic 200
        response (no user enumeration) instead of leaking a 404."""
        with patch(
            "app.api.v1.domains.auth.endpoints.auth.send_reset_password_email"
        ) as mock_send:
            response = client.post(
                "/api/v1/auth/password-recovery/nonexistent@example.com"
            )
            assert response.status_code == 200
            data = response.json()
            assert "msg" in data
            mock_send.assert_not_called()

    def test_reset_password_success(self, client: TestClient, test_user: dict, db: Session):
        """Test resetting password with valid token."""
        new_password = "NewSecurePass123!"

        with patch(
            "app.api.v1.domains.auth.endpoints.auth.verify_password_reset_token",
            return_value=test_user["email"],
        ):
            response = client.post(
                "/api/v1/auth/reset-password/",
                json={"token": "valid-test-token", "new_password": new_password},
            )
            assert response.status_code == 200
            data = response.json()
            assert "Password updated successfully" in data["msg"]

        # Verify login works with new password
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user["email"], "password": new_password},
        )
        assert login_response.status_code == 200

        # Verify old password no longer works
        old_login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user["email"], "password": test_user["password"]},
        )
        assert old_login_response.status_code == 400

    def test_reset_password_invalid_token(self, client: TestClient):
        """Test resetting password with invalid token returns 400."""
        response = client.post(
            "/api/v1/auth/reset-password/",
            json={"token": "bogus-token-value", "new_password": "NewSecurePass123!"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid token" in data["detail"]

    def test_reset_password_malformed_token(self, client: TestClient):
        """Test resetting password with malformed JWT returns 400."""
        response = client.post(
            "/api/v1/auth/reset-password/",
            json={"token": "not.a.valid.jwt", "new_password": "NewSecurePass123!"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid token" in data["detail"]

    def test_reset_password_real_token_roundtrip(
        self, client: TestClient, test_user: dict, db: Session
    ):
        """Test resetting password using a REAL token generated by
        generate_password_reset_token and verified by verify_password_reset_token
        (no mocking of the verification step).

        This directly exercises the sub/email JWT-claim round trip that broke
        in production before this session (verify_password_reset_token read
        the wrong claim key), so a regression here is caught without relying
        on the mocked test_reset_password_success test above.
        """
        new_password = "AnotherSecurePass456!"
        token = generate_password_reset_token(test_user["email"])

        # Prove the round trip works end-to-end before hitting the endpoint.
        assert verify_password_reset_token(token) == test_user["email"]

        response = client.post(
            "/api/v1/auth/reset-password/",
            json={"token": token, "new_password": new_password},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Password updated successfully" in data["msg"]

        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user["email"], "password": new_password},
        )
        assert login_response.status_code == 200

    def test_login_rate_limit_returns_429_with_valid_json_body(
        self, client: TestClient, test_user: dict
    ):
        """Test that exceeding the auth rate limit returns a real 429 response
        whose body parses cleanly as JSON.

        Regression test: the rate-limit exception handler used to return a
        plain dict instead of a Response, which crashed with a TypeError on
        every real 429 in production. This test hits the actual limiter path
        and asserts both the status code and that response.json() doesn't
        raise, which is exactly what would have caught the old bug.
        """
        limit = settings.RATE_LIMIT_AUTH_PER_MINUTE

        last_response = None
        for _ in range(limit + 5):
            last_response = client.post(
                "/api/v1/auth/login",
                data={
                    "username": test_user["email"],
                    "password": "wrongpassword123",
                },
            )
            if last_response.status_code == 429:
                break

        assert last_response.status_code == 429
        # This must not raise — the old bug crashed here with a TypeError
        # because the handler returned a dict instead of a Response.
        body = last_response.json()
        assert body is not None
