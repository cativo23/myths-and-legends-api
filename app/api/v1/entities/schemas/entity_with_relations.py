from pydantic import BaseModel, Field

from app.api.v1.entities.schemas.entity import Entity


class EntityRelationSummary(BaseModel):
    """Summary of a relation between two entities."""

    id: int = Field(
        ...,
        title="Relation ID",
        description="Unique identifier for the relation",
        examples=[1],
    )
    relation_type: str = Field(
        ...,
        title="Relation Type",
        description="Type of relationship (e.g., parent-child, sibling, enemy)",
        examples=["parent-of", "sibling-of", "enemy-of"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of the relationship",
        examples=["Anubis is the son of Osiris"],
    )
    related_entity_id: int = Field(
        ...,
        title="Related Entity ID",
        description="ID of the related entity",
        examples=[2],
    )
    related_entity_name: str = Field(
        ...,
        title="Related Entity Name",
        description="Name of the related entity",
        examples=["Osiris"],
    )
    direction: str = Field(
        ...,
        title="Direction",
        description="Direction of the relation relative to the current entity",
        examples=["origin", "destination"],
    )


class EntityWithRelations(Entity):
    """Entity schema including its full relation graph.

    Extends Entity with a list of all relations to other entities.
    """

    relations: list[EntityRelationSummary] = Field(
        default=[],
        title="Relations",
        description="List of relations to other entities",
    )
