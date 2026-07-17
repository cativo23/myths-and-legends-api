from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload

from app.api.common.services.base_service import CRUDBaseService
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
        if relation_type in [
            RelationType.SIBLINGS,
            RelationType.ALLIES,
            RelationType.ENEMIES,
        ]:
            reverse = EntityRelation(
                entity_origin_id=destination_id,
                entity_destination_id=origin_id,
                relation_type=relation_type,
                description=description,
            )
            db.add(reverse)

        db.commit()
        return forward, reverse
