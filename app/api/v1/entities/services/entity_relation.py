from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.entities.models.entity_relation import EntityRelation, RelationType
from app.api.v1.entities.schemas.entity_relation import (
    EntityRelationCreate,
    EntityRelationUpdate,
)


class EntityRelationService(
    CRUDBaseService[EntityRelation, EntityRelationCreate, EntityRelationUpdate]
):
    def __init__(self):
        super().__init__(EntityRelation)

    def get_by_entity(self, db: Session, *, entity_id: int) -> list[EntityRelation]:
        """Get all relations for an entity (both directions)"""
        stmt = select(EntityRelation).where(
            or_(
                EntityRelation.entity_origin_id == entity_id,
                EntityRelation.entity_destination_id == entity_id,
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
    ) -> tuple[EntityRelation, EntityRelation | None]:
        """
        Create bidirectional relation if symmetric (SIBLINGS, ALLIES, ENEMIES).
        Returns (forward_relation, reverse_relation or None)
        """
        forward = EntityRelation(
            entity_origin_id=origin_id,
            entity_destination_id=destination_id,
            relation_type=relation_type,
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
            )
            db.add(reverse)

        db.commit()
        return forward, reverse
