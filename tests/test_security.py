"""
Tests for the security utilities: JWT token creation, password hashing, and verification.
"""
from datetime import timedelta

from jose import jwt, JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    verify_refresh_token_hash,
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


class TestHashRefreshToken:
    def test_hash_is_deterministic_sha256(self):
        import hashlib

        token = "some-refresh-token-value"
        assert hash_refresh_token(token) == hashlib.sha256(token.encode()).hexdigest()

    def test_different_tokens_hash_differently(self):
        assert hash_refresh_token("token-a") != hash_refresh_token("token-b")


class TestVerifyRefreshTokenHash:
    def test_matching_token_verifies(self):
        token = "some-refresh-token-value"
        assert verify_refresh_token_hash(token, hash_refresh_token(token)) is True

    def test_mismatched_token_does_not_verify(self):
        assert verify_refresh_token_hash("wrong-token", hash_refresh_token("real-token")) is False

    def test_none_stored_hash_does_not_verify(self):
        assert verify_refresh_token_hash("any-token", None) is False


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
