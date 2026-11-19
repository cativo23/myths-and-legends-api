import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from typing import Any, Union

import bcrypt
from jose import jwt

from app.core.config import settings

# Cost 12 matches every hash already stored; changing it needs a rehash plan.
_BCRYPT_ROUNDS = 12
# bcrypt only reads the first 72 bytes. bcrypt 5 raises on longer input, so we
# truncate explicitly to keep verifying hashes created from longer passwords.
_BCRYPT_MAX_BYTES = 72
ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    # A unique jti guards against two refresh tokens minted for the same
    # subject within the same second-resolution `exp` colliding into an
    # identical JWT (same header/payload/signature), which would silently
    # defeat single-use rotation.
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": uuid.uuid4().hex,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def hash_refresh_token(token: str) -> str:
    """SHA-256 digest of a refresh token for storage. Not bcrypt: a refresh
    token is already a high-entropy random JWT, not a guessable secret, so
    bcrypt's deliberate slowness buys nothing here and would only add
    latency to every refresh request."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token_hash(token: str, hashed: str | None) -> bool:
    """Constant-time comparison between a presented token's hash and the
    stored hash, so timing doesn't leak how many hex characters matched."""
    if not hashed:
        return False
    return hmac.compare_digest(hash_refresh_token(token), hashed)


def get_token_expiry(token: str) -> datetime:
    """Read a token's actual `exp` claim back out, so a response's
    `expires_at` field always matches the token's real expiry exactly
    instead of independently recomputing `now + delta` a moment later."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    return datetime.utcfromtimestamp(payload["exp"])


def _to_bcrypt_input(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            _to_bcrypt_input(plain_password), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Malformed stored hash: fail closed instead of surfacing an internal
        # error to the client.
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        _to_bcrypt_input(password), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    ).decode("ascii")
