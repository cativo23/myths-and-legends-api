from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import category
from app.api.v1.entities.models.category import Category
from app.api.v1.entities.schemas.category import Category as CategorySchema

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
async def list_categories(
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
async def get_category(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Category ID", examples=[1])],
):
    """Get category by ID."""
    db_category = category.get(db, item_id=id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category
