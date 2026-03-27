from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.domains.users.services.user import user as user_crud
from app.api.v1.domains.users.models.user import User as UserModel
from app.api.v1.domains.users.schemas.user import User as UserSchema
from app.api.v1.domains.users.schemas.token import Token
from app.api.v1.shared.deps import get_db, get_current_user
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import (
    generate_password_reset_token,
    send_reset_password_email,
    verify_password_reset_token,
)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema for OpenAPI documentation."""
    username: str = Field(..., description="User email address", examples=["user@example.com"])
    password: str = Field(..., description="User password", examples=["SecureP@ss123"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="OAuth2 compatible token login. Exchange username/password for an access token.",
    responses={
        200: {"description": "Successful login, token returned"},
        400: {"description": "Incorrect email/password or inactive user"},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "required": ["username", "password"],
                        "properties": {
                            "username": {
                                "type": "string",
                                "title": "Username",
                                "description": "User email address",
                                "example": "user@example.com"
                            },
                            "password": {
                                "type": "string",
                                "title": "Password",
                                "description": "User password",
                                "format": "password",
                                "example": "SecureP@ss123"
                            },
                        },
                    }
                }
            }
        }
    },
)
async def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, Any]:
    """
    OAuth2 compatible token login, get an access token for future requests.

    Rate limited to prevent brute force attacks.

    **Request Body:**
    - `username`: User email address
    - `password`: User password
    """
    user = user_crud.authenticate(
        db, email=form_data.username, password=form_data.password
    )

    if user is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user_crud.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "expires_at": datetime.utcnow() + access_token_expires,
        "token_type": "Bearer",
    }


@router.get(
    "/me",
    response_model=UserSchema,
    summary="Get Current User",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "Successful retrieval of user info"},
        401: {"description": "Unauthorized - No valid token provided"},
    },
)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Get current user information."""
    return current_user


@router.post(
    "/password-recovery/{email}",
    summary="Password Recovery",
    description="Initiate password recovery by sending a reset email to the user.",
    responses={
        200: {"description": "Password recovery email sent"},
        404: {"description": "User not found"},
    },
)
async def recover_password(
    email: str = Path(..., description="User email address", examples=["user@example.com"]),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Password Recovery.

    Rate limited to prevent abuse.
    """
    user = user_crud.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.post(
    "/reset-password/",
    summary="Reset Password",
    description="Reset password using a valid recovery token.",
    responses={
        200: {"description": "Password successfully updated"},
        400: {"description": "Invalid token or inactive user"},
        404: {"description": "User not found"},
    },
)
async def reset_password(
    token: str = Body(..., description="Password recovery token", examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]),
    new_password: str = Body(..., description="New password (min 8 characters)", examples=["NewSecureP@ss123"]),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Reset password using a valid recovery token.
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = user_crud.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not user_crud.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}
