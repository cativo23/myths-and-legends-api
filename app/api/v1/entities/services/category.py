from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.entities.models.category import Category
from app.api.v1.entities.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService(CRUDBaseService[Category, CategoryCreate, CategoryUpdate]):
    """Service for Category CRUD operations."""

    def get_with_entities(self, db: Session, *, id: int) -> Category | None:
        """Get category with entities"""
        stmt = (
            select(Category)
            .where(Category.id == id)
            .options(selectinload(Category.entities))
        )
        return db.execute(stmt).scalar_one_or_none()
