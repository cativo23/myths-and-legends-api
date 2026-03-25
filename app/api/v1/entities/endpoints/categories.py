from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.entities.services.category import CategoryService
from app.api.v1.entities.models.category import Category
from app.api.v1.entities.schemas.category import Category as CategorySchema

router = APIRouter(prefix="/categories", tags=["categories"])

category_service = CategoryService()


@router.get("/", response_model=list[CategorySchema])
def list_categories(db: Annotated[Session, Depends(get_db)]):
    """List all categories"""
    return db.query(Category).all()


@router.get("/{id}", response_model=CategorySchema)
def get_category(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get category by ID"""
    category = category_service.get(db, id=id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
