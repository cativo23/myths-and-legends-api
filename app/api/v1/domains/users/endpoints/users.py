from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi_pagination import Page, Params
from sqlalchemy.orm import Session

from app.api.v1.domains.users.models.user import User as UserModel
from app.api.v1.domains.users.schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
)
from app.api.v1.domains.users.services.user import user as user_service
from app.api.v1.shared.deps import get_db, get_current_active_superuser

router = APIRouter()


@router.get(
    "/",
    response_model=Page[UserSchema],
    summary="List Users",
    description="Retrieve a paginated list of users. Requires superuser privileges.",
    responses={
        200: {"description": "Successful retrieval of users"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
async def get_users(
    db: Session = Depends(get_db),
    page: int = Query(1, description="Page number", ge=1),
    size: int = Query(20, description="Items per page", ge=1, le=100),
    sort: str = Query(
        "email",
        description="Field to sort by",
        examples=["email", "full_name", "id", "created_at"],
    ),
    order: str = Query("asc", description="Sort order", examples=["asc", "desc"]),
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """List all users with pagination and sorting."""
    return user_service.get_all(db, params=Params(page=page, size=size))


@router.post(
    "/",
    response_model=UserSchema,
    status_code=201,
    summary="Create User",
    description="Create a new user. Requires superuser privileges.",
    responses={
        201: {"description": "User successfully created"},
        400: {"description": "Email already exists"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """Create a new user."""
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = user_service.create(db, obj_in=user_in)
    return user


@router.put(
    "/{user_id}",
    response_model=UserSchema,
    summary="Update User",
    description="Update an existing user by ID. Requires superuser privileges.",
    responses={
        200: {"description": "User successfully updated"},
        404: {"description": "User not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
async def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., description="User ID", examples=[1], gt=0),
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """Update a user."""
    user = user_service.get(db, item_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_service.update(db, db_obj=user, obj_in=user_in)
    return user


@router.get(
    "/{user_id}",
    response_model=UserSchema,
    summary="Get User",
    description="Retrieve a specific user by ID. Requires superuser privileges.",
    responses={
        200: {"description": "Successful retrieval of user"},
        404: {"description": "User not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
async def get_user(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., description="User ID", examples=[1], gt=0),
    current_user: UserModel = Depends(get_current_active_superuser),
) -> Any:
    """Get a user by ID."""
    user = user_service.get(db, item_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Delete User",
    description="Delete a user by ID. Requires superuser privileges.",
    responses={
        204: {"description": "User successfully deleted"},
        404: {"description": "User not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
async def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int = Path(..., description="User ID", examples=[1], gt=0),
    current_user: UserModel = Depends(get_current_active_superuser),
) -> None:
    """Delete a user."""
    user = user_service.get(db, item_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.remove(db, item_id=user_id)
