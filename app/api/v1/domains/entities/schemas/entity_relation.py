from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.domains.entities.enums import RelationType


class EntityRelationBase(BaseModel):
    relation_type: RelationType
    description: str | None = None


class EntityRelationCreate(EntityRelationBase):
    entity_origin_id: int
    entity_destination_id: int


class EntityRelationUpdate(BaseModel):
    relation_type: RelationType | None = None
    description: str | None = None


class EntityRelationInDB(EntityRelationBase):
    id: int
    entity_origin_id: int
    entity_destination_id: int
    model_config = ConfigDict(from_attributes=True)


class EntityRelation(EntityRelationInDB):
    entity_origin_name: str | None = None
    entity_destination_name: str | None = None
