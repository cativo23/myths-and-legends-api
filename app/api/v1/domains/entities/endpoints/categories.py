from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db, get_current_active_superuser
from app.api.v1.domains.entities.services import category
from app.api.v1.domains.entities.models.category import Category
from app.api.v1.domains.entities.schemas.category import (
    Category as CategorySchema,
    CategoryCreate,
    CategoryUpdate,
)
from app.api.v1.domains.users.models.user import User as UserModel

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "/",
    response_model=Page[CategorySchema],
    summary="List Categories",
    description="Retrieve a paginated list of categories for classifying entities (e.g., Deity, Creature, Place).",
    responses={
        200: {"description": "Successful retrieval of categories"},
    },
)
def list_categories(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    sort: Annotated[
        Literal["name", "id"],
        Query(description="Sort field", examples=["name", "id"]),
    ] = "name",
    order: Annotated[
        str, Query(description="Sort order (asc, desc)", examples=["asc", "desc"])
    ] = "asc",
):
    """List all categories, paginated and sorted at the database level."""
    sort_column = getattr(Category, sort)
    stmt = select(Category).order_by(
        sort_column.desc() if order.lower() == "desc" else sort_column.asc()
    )
    return paginate(db, stmt, Params(page=page, size=size))


@router.get(
    "/{id}",
    response_model=CategorySchema,
    summary="Get Category",
    description="Retrieve a specific category by ID.",
    responses={
        200: {"description": "Successful retrieval of category"},
        404: {"description": "Category not found"},
    },
)
def get_category(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Category ID", examples=[1])],
):
    """Get category by ID."""
    db_category = category.get(db, item_id=id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.post(
    "/",
    response_model=CategorySchema,
    status_code=201,
    summary="Create Category",
    description="Create a new category. Requires superuser privileges.",
    responses={
        201: {"description": "Category successfully created"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def create_category(
    db: Annotated[Session, Depends(get_db)],
    category_in: CategoryCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Create a new category. Requires superuser privileges."""
    return category.create(db, obj_in=category_in)


@router.put(
    "/{id}",
    response_model=CategorySchema,
    summary="Update Category",
    description="Update an existing category by ID. Requires superuser privileges.",
    responses={
        200: {"description": "Category successfully updated"},
        404: {"description": "Category not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def update_category(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Category ID", examples=[1])],
    category_in: CategoryUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Update a category. Requires superuser privileges."""
    db_category = category.get(db, item_id=id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category.update(db, db_obj=db_category, obj_in=category_in)


@router.delete(
    "/{id}",
    status_code=204,
    summary="Delete Category",
    description="Delete a category by ID. Requires superuser privileges.",
    responses={
        204: {"description": "Category successfully deleted"},
        404: {"description": "Category not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def delete_category(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Category ID", examples=[1])],
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Delete a category. Requires superuser privileges."""
    db_category = category.get(db, item_id=id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.remove(db, item_id=id)
