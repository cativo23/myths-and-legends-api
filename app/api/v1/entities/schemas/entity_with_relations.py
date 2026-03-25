from pydantic import BaseModel

from app.api.v1.entities.schemas.entity import Entity


class EntityRelationSummary(BaseModel):
    """Simplified relation info for entity responses"""

    id: int
    relation_type: str
    description: str | None
    related_entity_id: int
    related_entity_name: str
    direction: str  # "origin" or "destination"


class EntityWithRelations(Entity):
    """Entity with full relation graph"""

    relations: list[EntityRelationSummary] = []
