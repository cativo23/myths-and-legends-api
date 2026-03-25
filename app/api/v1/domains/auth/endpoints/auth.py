from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.v1.domains.users.services.user import user as user_crud
from app.api.v1.domains.users.models.user import User as UserModel
from app.api.v1.domains.users.schemas.user import User as UserSchema
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


@router.post("/login", response_model=Any)
def login_access_token(
        db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
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


@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: UserModel = Depends(get_current_user)) -> Any:
    """
    Get current user information
    """
    return current_user


@router.post("/password-recovery/{email}", response_model=Any)
def recover_password(email: str, db: Session = Depends(get_db)) -> Any:
    """
    Password Recovery
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


@router.post("/reset-password/", response_model=Any)
def reset_password(
        token: str = Body(...),
        new_password: str = Body(...),
        db: Session = Depends(get_db),
) -> Any:
    """
    Reset password
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
