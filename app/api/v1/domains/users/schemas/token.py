from typing import Optional, Any

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    expires_at: Any
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None
