import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Union

# Patch bcrypt compatibility issue with passlib (bcrypt >= 4.1 dropped the
# __about__.__version__ attribute passlib's backend probe relies on, and
# changed truncation behavior for passwords > 72 bytes). Must run before
# passlib is imported.
import bcrypt as _bcrypt_lib


class _BcryptAbout:
    __version__ = _bcrypt_lib.__version__


_bcrypt_lib.__about__ = _BcryptAbout()
_original_bcrypt_hashpw = _bcrypt_lib.hashpw


def _safe_bcrypt_hashpw(password, salt):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _original_bcrypt_hashpw(password, salt)


_bcrypt_lib.hashpw = _safe_bcrypt_hashpw

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
