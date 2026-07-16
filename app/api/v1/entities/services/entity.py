from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import Select

from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination.ext.sqlalchemy import paginate as paginate_sqlalchemy

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.entities.models.entity import Entity
from app.api.v1.entities.models.entity_relation import EntityRelation
from app.api.v1.entities.schemas.entity import EntityCreate, EntityUpdate
from app.api.v1.entities.enums import EntityTypeName, CategoryName


class EntityService(CRUDBaseService[Entity, EntityCreate, EntityUpdate]):
    """Service for Entity CRUD operations."""

    def _get_base_query(self) -> Select:
        """Build base query with common eager loading"""
        return select(Entity).options(
            selectinload(Entity.category),
            selectinload(Entity.entity_type),
            selectinload(Entity.characteristics),
            selectinload(Entity.locations),
            selectinload(Entity.sources),
        )

    def get(self, db: Session, *, item_id: int) -> Entity | None:
        """Get entity by ID with all nested relations"""
        stmt = self._get_base_query().where(Entity.id == item_id)
        return db.execute(stmt).scalar_one_or_none()

    def _apply_filters(
        self,
        stmt: Select,
        *,
        entity_type: EntityTypeName | None = None,
        category: CategoryName | None = None,
        is_active: bool | None = True,
    ) -> Select:
        """Apply the common entity_type/category/is_active filters to a query."""
        filters = []
        if entity_type:
            filters.append(Entity.entity_type.has(name=entity_type))
        if category:
            filters.append(Entity.category.has(name=category))
        if is_active is not None:
            filters.append(Entity.is_active == is_active)

        if filters:
            stmt = stmt.where(and_(*filters))
        return stmt

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
        stmt = self._apply_filters(
            self._get_base_query(),
            entity_type=entity_type,
            category=category,
            is_active=is_active,
        )
        stmt = stmt.order_by(Entity.id).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    def get_paginated(
        self,
        db: Session,
        *,
        entity_type: EntityTypeName | None = None,
        category: CategoryName | None = None,
        is_active: bool | None = True,
        params: AbstractParams | None = None,
    ) -> AbstractPage:
        """Get entities with filters, paginated at the DB level.

        Unlike `get_multi`, this performs a real SQL COUNT + LIMIT/OFFSET via
        fastapi-pagination's SQLAlchemy extension, instead of slicing an
        already-limited Python list a second time (see the double-pagination
        bug this replaces in the `list_entities` endpoint).

        `params` should be the `Params(page=page, size=size)` built from the
        endpoint's own page/size query params — the endpoint also validates
        entity_type/category/is_active, so it can't rely on fastapi-
        pagination's auto-injected Params context (that would silently apply
        its own default page size instead of this endpoint's).
        """
        stmt = self._apply_filters(
            self._get_base_query(),
            entity_type=entity_type,
            category=category,
            is_active=is_active,
        )
        stmt = stmt.order_by(Entity.id)
        return paginate_sqlalchemy(db, stmt, params)

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
