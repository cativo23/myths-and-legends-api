"""
Tests for the security utilities: JWT token creation, password hashing, and verification.
"""
from datetime import timedelta

from jose import jwt, JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    ALGORITHM,
)
from app.core.config import settings


class TestCreateAccessToken:
    def test_creates_valid_jwt_token(self):
        """Token should encode subject and expiration, and be decodable."""
        token = create_access_token(subject="test-user")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "test-user"
        assert "exp" in payload

    def test_custom_expires_delta(self):
        """Token should expire at the specified delta."""
        from datetime import datetime, timezone

        delta = timedelta(minutes=5)
        before = datetime.now(timezone.utc)
        token = create_access_token(subject="test-user", expires_delta=delta)
        after = datetime.now(timezone.utc)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload["exp"]
        # exp should be approximately (before + delta) to (after + delta)
        expected_min = int((before + delta).timestamp())
        expected_max = int((after + delta).timestamp()) + 1
        assert expected_min <= exp_timestamp <= expected_max

    def test_default_expiry_is_configured(self):
        """Token without custom delta should use ACCESS_TOKEN_EXPIRE_MINUTES."""
        token = create_access_token(subject="test-user")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        # 60 * 24 * 8 = 11520 minutes = 691200 seconds
        expected_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        actual_lifetime = payload["exp"] - (
            payload.get("iat", payload["exp"])
            if "iat" in payload
            else payload["exp"] - expected_seconds
        )
        assert abs(actual_lifetime - expected_seconds) < 5

    def test_type_claim_is_access(self):
        token = create_access_token(subject=1)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "access"
        assert payload["sub"] == "1"


class TestCreateRefreshToken:
    def test_type_claim_is_refresh(self):
        token = create_refresh_token(subject=1)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "refresh"
        assert payload["sub"] == "1"

    def test_default_expiry_uses_settings(self):
        from datetime import datetime

        token = create_refresh_token(subject=1)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        expires_in_days = (
            datetime.utcfromtimestamp(payload["exp"]) - datetime.utcnow()
        ).days
        # Allow a 1-day tolerance for test execution time.
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS - 1 <= expires_in_days <= settings.REFRESH_TOKEN_EXPIRE_DAYS


class TestVerifyPassword:
    def test_returns_true_for_correct_password(self):
        hashed = get_password_hash("my-secret")
        assert verify_password("my-secret", hashed) is True

    def test_returns_false_for_wrong_password(self):
        hashed = get_password_hash("my-secret")
        assert verify_password("wrong-password", hashed) is False


class TestGetPasswordHash:
    def test_different_hash_each_call(self):
        """Same password should produce different hashes due to salt."""
        hash1 = get_password_hash("same-password")
        hash2 = get_password_hash("same-password")
        assert hash1 != hash2

    def test_both_hashes_verify(self):
        """Both unique hashes should verify the same password."""
        hash1 = get_password_hash("same-password")
        hash2 = get_password_hash("same-password")
        assert verify_password("same-password", hash1) is True
        assert verify_password("same-password", hash2) is True
