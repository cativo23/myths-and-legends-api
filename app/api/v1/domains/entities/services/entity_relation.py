from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.common.services.base_service import (
    CRUDBaseService,
    raise_for_integrity_error,
)
from app.api.v1.domains.entities.enums import SYMMETRIC_RELATION_TYPES
from app.api.v1.domains.entities.models.entity_relation import (
    EntityRelation,
    RelationType,
)
from app.api.v1.domains.entities.schemas.entity_relation import (
    EntityRelationCreate,
    EntityRelationUpdate,
)


class EntityRelationService(
    CRUDBaseService[EntityRelation, EntityRelationCreate, EntityRelationUpdate]
):
    """Service for EntityRelation CRUD operations."""

    def get_by_entity(self, db: Session, *, entity_id: int) -> list[EntityRelation]:
        """Get all relations for an entity (both directions), eager-loading
        entity_origin/entity_destination to avoid an N+1 when callers access
        the related entity for every relation (see EntityService.get_relations_graph
        for the same eager-loading shape)."""
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

    def get_for_entity(
        self, db: Session, *, entity_id: int, relation_id: int
    ) -> EntityRelation | None:
        """Get a relation by id only if it involves the entity (as origin or
        destination), the same set get_by_entity lists. A relation of other
        entities is indistinguishable from a missing one, so callers cannot
        probe ids through this entity."""
        stmt = select(EntityRelation).where(
            EntityRelation.id == relation_id,
            or_(
                EntityRelation.entity_origin_id == entity_id,
                EntityRelation.entity_destination_id == entity_id,
            ),
        )
        return db.execute(stmt).scalar_one_or_none()

    def remove_with_reverse(self, db: Session, *, relation: EntityRelation) -> None:
        """Delete a relation and, for symmetric types, its reverse row, in one
        commit so a failure never leaves a one-sided pair. A missing reverse
        (legacy data) is tolerated."""
        db.delete(relation)
        if relation.relation_type in SYMMETRIC_RELATION_TYPES:
            reverse = db.execute(
                select(EntityRelation).where(
                    EntityRelation.entity_origin_id == relation.entity_destination_id,
                    EntityRelation.entity_destination_id == relation.entity_origin_id,
                    EntityRelation.relation_type == relation.relation_type,
                )
            ).scalar_one_or_none()
            if reverse is not None:
                db.delete(reverse)
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

    def create_bidirectional(
        self,
        db: Session,
        *,
        origin_id: int,
        destination_id: int,
        relation_type: RelationType,
        description: str | None = None,
    ) -> tuple[EntityRelation, EntityRelation | None]:
        """
        Create bidirectional relation if symmetric (SIBLINGS, ALLIES, ENEMIES).
        Returns (forward_relation, reverse_relation or None)
        """
        forward = EntityRelation(
            entity_origin_id=origin_id,
            entity_destination_id=destination_id,
            relation_type=relation_type,
            description=description,
        )
        db.add(forward)

        # Create reverse for symmetric relations
        reverse = None
        if relation_type in SYMMETRIC_RELATION_TYPES:
            reverse = EntityRelation(
                entity_origin_id=destination_id,
                entity_destination_id=origin_id,
                relation_type=relation_type,
                description=description,
            )
            db.add(reverse)

        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise_for_integrity_error(EntityRelation, error)
        db.refresh(forward)
        if reverse:
            db.refresh(reverse)
        return forward, reverse
