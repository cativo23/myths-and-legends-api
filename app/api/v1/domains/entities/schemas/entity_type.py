from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.domains.entities.enums import EntityTypeName


class EntityTypeBase(BaseModel):
    """Base entity type properties.

    Entity types classify entities by what they are
    (CHARACTER, PLACE, OBJECT, GROUP or EVENT).
    """

    name: EntityTypeName = Field(
        ...,
        title="Name",
        description="Kind of entity: CHARACTER, PLACE, OBJECT, GROUP or EVENT",
        examples=["CHARACTER", "PLACE", "OBJECT", "GROUP", "EVENT"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of this kind of entity",
        examples=["A being from Salvadoran folklore, such as El Cipitío"],
    )


class EntityTypeCreate(EntityTypeBase):
    """Schema for creating a new entity type."""

    pass


class EntityTypeUpdate(BaseModel):
    """Schema for updating an existing entity type."""

    name: EntityTypeName | None = Field(
        None,
        title="Name",
        description="Kind of entity: CHARACTER, PLACE, OBJECT, GROUP or EVENT",
        examples=["CHARACTER"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of this kind of entity",
        examples=["A being from Salvadoran folklore, such as El Cipitío"],
    )


class EntityTypeInDB(EntityTypeBase):
    """Base schema for entity type data stored in database."""

    id: int = Field(
        ...,
        title="ID",
        description="Unique entity type identifier",
        examples=[1],
    )
    model_config = ConfigDict(from_attributes=True)


class EntityType(EntityTypeInDB):
    """Schema returned by the API for entity type data."""

    entity_count: int = Field(
        default=0,
        title="Entity Count",
        description="Number of entities with this type",
        examples=[15],
    )
