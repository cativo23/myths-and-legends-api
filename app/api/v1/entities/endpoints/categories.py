from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import category
from app.api.v1.entities.models.category import Category
from app.api.v1.entities.schemas.category import Category as CategorySchema

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategorySchema])
async def list_categories(
    db: Annotated[Session, Depends(get_db)],
    sort: Annotated[str | None, Query(description="Sort field")] = "name",
    order: Annotated[str, Query(description="Sort order")] = "asc",
):
    """List all categories"""
    categories = db.query(Category).all()

    # Sort results
    if order.lower() == "desc":
        return sorted(categories, key=lambda x: getattr(x, sort, x.id), reverse=True)
    return sorted(categories, key=lambda x: getattr(x, sort, x.id))


@router.get("/{id}", response_model=CategorySchema)
async def get_category(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get category by ID"""
    db_category = category.get(db, id=id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category
