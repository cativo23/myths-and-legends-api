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


class CreateRelationRequest(BaseModel):
    """Request body for POST /entities/{id}/relations — the origin entity ID
    comes from the URL path, so only the destination and relation type are
    needed here."""

    entity_destination_id: int = Field(
        ...,
        title="Destination Entity ID",
        description="ID of the entity this relation points to",
        examples=[2],
    )
    relation_type: RelationType = Field(
        ...,
        title="Relation Type",
        description="Type of relation between the two entities",
        examples=["SIBLINGS", "ENEMIES", "MOTHER_CHILD"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Optional description of the relation",
        examples=["The Cadejos represent the eternal struggle between good and evil"],
    )
