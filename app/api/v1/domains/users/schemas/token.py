from typing import Optional, Any

from pydantic import BaseModel, Field


class Token(BaseModel):
    """JWT token response for authentication endpoints.

    Returned when a user successfully logs in.
    """

    access_token: str = Field(
        ...,
        title="Access Token",
        description="JWT access token for authenticated requests",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    refresh_token: str = Field(
        ...,
        title="Refresh Token",
        description="Long-lived JWT used to obtain a new access token via /auth/refresh",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    expires_at: Any = Field(
        ...,
        title="Expires At",
        description="Timestamp when the token expires",
        examples=["2024-01-20T10:30:00Z"],
    )
    token_type: str = Field(
        ...,
        title="Token Type",
        description="Type of token (Bearer)",
        examples=["Bearer"],
    )


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: Optional[int] = Field(
        None,
        title="Subject",
        description="User ID encoded in the token",
        examples=[1],
    )
