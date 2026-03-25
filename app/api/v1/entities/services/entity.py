from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import Select

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.entities.models.entity import Entity
from app.api.v1.entities.models.entity_relation import EntityRelation
from app.api.v1.entities.schemas.entity import EntityCreate, EntityUpdate
from app.api.v1.entities.enums import EntityTypeName, CategoryName


class EntityService(CRUDBaseService[Entity, EntityCreate, EntityUpdate]):
    def __init__(self):
        super().__init__(Entity)

    def _get_base_query(self) -> Select:
        """Build base query with common eager loading"""
        return select(Entity).options(
            selectinload(Entity.category),
            selectinload(Entity.entity_type),
            selectinload(Entity.characteristics),
            selectinload(Entity.locations),
            selectinload(Entity.sources),
        )

    def get(self, db: Session, *, id: int) -> Entity | None:
        """Get entity by ID with all nested relations"""
        stmt = self._get_base_query().where(Entity.id == id)
        return db.execute(stmt).scalar_one_or_none()

    def get_multi(
        self,
        db: Session,
        *,
        entity_type: EntityTypeName | None = None,
        category: CategoryName | None = None,
        is_active: bool | None = True,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Entity]:
        """Get multiple entities with filters"""
        stmt = self._get_base_query()

        # Apply filters
        filters = []
        if entity_type:
            filters.append(Entity.entity_type.has(name=entity_type))
        if category:
            filters.append(Entity.category.has(name=category))
        if is_active is not None:
            filters.append(Entity.is_active == is_active)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    def search(self, db: Session, *, term: str) -> list[Entity]:
        """Search entities by name, alternative_names, description, or origin"""
        stmt = self._get_base_query().where(
            or_(
                Entity.name.ilike(f"%{term}%"),
                Entity.description.ilike(f"%{term}%"),
                Entity.origin.ilike(f"%{term}%"),
            )
        )
        return db.execute(stmt).scalars().all()

    def get_relations_graph(
        self, db: Session, *, entity_id: int
    ) -> list[EntityRelation]:
        """Get all relations where entity appears (as origin OR destination)"""
        stmt = (
            select(EntityRelation)
            .where(
                or_(
                    EntityRelation.entity_origin_id == entity_id,
                    EntityRelation.entity_destination_id == entity_id,
                )
            )
            .options(
                selectinload(EntityRelation.entity_origin),
                selectinload(EntityRelation.entity_destination),
            )
        )
        return db.execute(stmt).scalars().all()
