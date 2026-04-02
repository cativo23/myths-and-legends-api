from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import category
from app.api.v1.entities.models.category import Category
from app.api.v1.entities.schemas.category import Category as CategorySchema

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "/",
    response_model=List[CategorySchema],
    summary="List Categories",
    description="Retrieve all categories for classifying entities (e.g., Deity, Creature, Place).",
    responses={
        200: {"description": "Successful retrieval of categories"},
    },
)
async def list_categories(
    db: Annotated[Session, Depends(get_db)],
    sort: Annotated[
        str | None, Query(description="Sort field", examples=["name", "id"])
    ] = "name",
    order: Annotated[
        str, Query(description="Sort order (asc, desc)", examples=["asc", "desc"])
    ] = "asc",
):
    """List all categories."""
    categories = db.query(Category).all()

    # Sort results
    if order.lower() == "desc":
        return sorted(categories, key=lambda x: getattr(x, sort, x.id), reverse=True)
    return sorted(categories, key=lambda x: getattr(x, sort, x.id))


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
    db_category = category.get(db, id=id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category
