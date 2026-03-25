from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params, paginate
from sqlalchemy.orm import Session

from app.api.v1.domains.users.models.user import User as UserModel
from app.api.v1.domains.users.schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
)
from app.api.v1.domains.users.services.user import user as user_service
from app.api.v1.shared.deps import get_db, get_current_active_superuser
from app.api.common.pagination.json_api_page import JsonApiPage
router = APIRouter()


@router.get("/", response_model=Page[UserSchema])
async def get_users(
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
    sort: str = "email",
    order: str = "asc",
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve users.

    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `size`: Items per page (default: 20, max: 100)
    - `sort`: Field to sort by (email, full_name, id, created_at)
    - `order`: Sort order (asc, desc)
    """
    users = user_service.get_multi(db, skip=(page - 1) * size, limit=size)
    return paginate(users, Params(page=page, size=size))


@router.post("/", response_model=UserSchema, status_code=201)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = user_service.create(db, obj_in=user_in)
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_service.update(db, db_obj=user, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """
    Get user by ID.
    """
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> None:
    """
    Delete user by ID.
    """
    user = user_service.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.remove(db, id=user_id)
