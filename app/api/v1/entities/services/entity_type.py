from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.schemas.entity_type import EntityTypeCreate, EntityTypeUpdate


class EntityTypeService(CRUDBaseService[EntityType, EntityTypeCreate, EntityTypeUpdate]):
    def __init__(self):
        super().__init__(EntityType)

    def get_with_entities(self, db: Session, *, id: int) -> EntityType | None:
        """Get entity type with entities"""
        stmt = select(EntityType).where(EntityType.id == id).options(
            selectinload(EntityType.entities)
        )
        return db.execute(stmt).scalar_one_or_none()
