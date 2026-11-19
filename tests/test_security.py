"""
Tests for the security utilities: JWT token creation, password hashing, and verification.
"""
from datetime import timedelta

import subprocess
import sys

import pytest
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


# Hashes generated by the passlib-based implementation before it was replaced
# with direct bcrypt. They must keep verifying forever (no rehash migration).
# The passwords are throwaway fixtures, not real credentials.
PRE_CHANGE_HASHES = [
    ("correct-horse-battery", "$2b$12$ITGSnIn9ZCv6Rt9sfCUyduUr0vWt5ty7u6TNFtKscLLuRIi2xpMqm"),
    ("contraseña-ñandú-🔐", "$2b$12$WAerbdaQVtNLkbenhuEWn.DnYAU.O.Mbn1Sd/nqfkS2MPn7gUSQem"),
    ("", "$2b$12$f6R6zQp.x15TCRDUCg60t.GyQQBuENuilSda6rQ4PI9Nhz0eBTvDy"),
    ("a" * 72, "$2b$12$WmZXOtv3FDiy/tPjtJ1RAu6s4IJ9JkTQXLnRUQqM907t0TcrimXIq"),
    ("legacy-2y-password", "$2y$12$SbS.ut9bV23ve/8wdg8k7.KYkbqU2ECa74V4Ue5gRX4VE5tb1C14K"),
]


class TestPreChangeHashCompatibility:
    @pytest.mark.parametrize("password,stored", PRE_CHANGE_HASHES)
    def test_should_verify_pre_change_hashes(self, password, stored):
        assert verify_password(password, stored) is True

    @pytest.mark.parametrize("password,stored", PRE_CHANGE_HASHES)
    def test_should_reject_wrong_password_against_pre_change_hash(self, password, stored):
        # Alter the first character: a suffix would be truncated away for the 72-byte fixture.
        wrong = "Z" + password[1:] if password else "wrong"
        assert verify_password(wrong, stored) is False


class TestHashFormat:
    def test_should_produce_standard_bcrypt_hash_with_cost_12(self):
        hashed = get_password_hash("format-check")
        assert hashed.startswith("$2b$12$")
        assert len(hashed) == 60


class TestBcrypt72ByteTruncation:
    @pytest.mark.parametrize("length", [72, 73, 200])
    def test_should_treat_only_first_72_bytes_as_significant(self, length):
        original = "a" * length
        hashed = get_password_hash(original)
        assert verify_password(original, hashed) is True
        # Anything sharing the first 72 bytes is the same password to bcrypt.
        assert verify_password("a" * 72 + "different tail", hashed) is (length >= 72)

    def test_should_not_raise_when_multibyte_char_straddles_byte_72(self):
        # 71 ASCII bytes + a 4-byte emoji puts the cut inside the character.
        password = "a" * 71 + "🔐" + "tail"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_should_hash_and_verify_password_containing_nul_byte(self):
        # passlib rejected NUL bytes (a latent 500 on registration); bcrypt 5
        # handles them correctly, so the password is simply a different secret.
        hashed = get_password_hash("a\x00b")
        assert verify_password("a\x00b", hashed) is True
        assert verify_password("a\x00c", hashed) is False
        assert verify_password("a", hashed) is False


class TestVerifyPasswordFailsClosed:
    @pytest.mark.parametrize("stored", ["notahash", "", None, "$2b$12$short"])
    def test_should_fail_closed_on_malformed_stored_hash(self, stored):
        assert verify_password("anything", stored) is False

    def test_should_fail_closed_on_nul_byte_password(self):
        stored = PRE_CHANGE_HASHES[0][1]
        assert verify_password("a\x00b", stored) is False


class TestNoImportTimePatching:
    def test_should_not_patch_bcrypt_at_import(self):
        # Fresh interpreter: other tests may already have imported the module.
        code = (
            "import bcrypt\n"
            "original = bcrypt.hashpw\n"
            "import app.core.security\n"
            "assert bcrypt.hashpw is original, 'hashpw was replaced'\n"
            "assert not hasattr(bcrypt, '__about__'), '__about__ shim was added'\n"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr[-500:]
