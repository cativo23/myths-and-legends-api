from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntityBase(BaseModel):
    """Base entity properties shared across schemas.

    Entities represent mythological characters, creatures, places, or objects
    from various mythologies and legends.
    """

    name: str = Field(
        ...,
        title="Name",
        description="Primary name of the entity",
        min_length=1,
        max_length=255,
        examples=["Anubis", "Zeus", "Quetzalcoatl"],
    )
    alternative_names: list[str] | None = Field(
        None,
        title="Alternative Names",
        description="Other names or aliases for this entity",
        examples=[["Anpu", "Inpu"]],
    )
    category_id: int = Field(
        ...,
        title="Category ID",
        description="ID of the entity category (e.g., Deity, Creature, Place)",
        examples=[1],
    )
    entity_type_id: int = Field(
        ...,
        title="Entity Type ID",
        description="ID of the entity type (e.g., Egyptian, Greek, Aztec)",
        examples=[2],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Detailed description of the entity",
        examples=["God of mummification and the afterlife"],
    )
    origin: str | None = Field(
        None,
        title="Origin",
        description="Origin story or background of the entity",
        examples=["Born from the primordial waters of Nun"],
    )
    behavior: str | None = Field(
        None,
        title="Behavior",
        description="Typical behavior or characteristics",
        examples=[
            "Guides souls to the underworld, weighs hearts against Ma'at feather"
        ],
    )
    image_url: str | None = Field(
        None,
        title="Image URL",
        description="URL to an image representing the entity",
        max_length=500,
        examples=["https://example.com/images/anubis.jpg"],
    )
    is_active: bool = Field(
        True,
        title="Is Active",
        description="Whether the entity is active in the system",
        examples=[True],
    )


class EntityCreate(EntityBase):
    """Schema for creating a new entity.

    Note: Characteristics, locations, and sources are handled separately
    via their respective endpoints after entity creation.
    """

    pass


class EntityUpdate(BaseModel):
    """Schema for updating an existing entity.

    All fields are optional - only provided fields will be updated.
    """

    name: str | None = Field(
        None,
        title="Name",
        description="Primary name of the entity",
        min_length=1,
        max_length=255,
        examples=["Anubis"],
    )
    alternative_names: list[str] | None = Field(
        None,
        title="Alternative Names",
        description="Other names or aliases for this entity",
        examples=[["Anpu", "Inpu"]],
    )
    category_id: int | None = Field(
        None,
        title="Category ID",
        description="ID of the entity category",
        examples=[1],
    )
    entity_type_id: int | None = Field(
        None,
        title="Entity Type ID",
        description="ID of the entity type",
        examples=[2],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Detailed description of the entity",
        examples=["God of mummification and the afterlife"],
    )
    origin: str | None = Field(
        None,
        title="Origin",
        description="Origin story or background of the entity",
        examples=["Born from the primordial waters of Nun"],
    )
    behavior: str | None = Field(
        None,
        title="Behavior",
        description="Typical behavior or characteristics",
        examples=["Guides souls to the underworld"],
    )
    image_url: str | None = Field(
        None,
        title="Image URL",
        description="URL to an image representing the entity",
        max_length=500,
        examples=["https://example.com/images/anubis.jpg"],
    )
    is_active: bool | None = Field(
        None,
        title="Is Active",
        description="Whether the entity is active in the system",
        examples=[True],
    )


class EntityInDB(EntityBase):
    """Base schema for entity data stored in database."""

    id: int = Field(
        ...,
        title="ID",
        description="Unique entity identifier",
        examples=[1],
    )
    created_at: datetime = Field(
        ...,
        title="Created At",
        description="Timestamp when the entity was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    model_config = ConfigDict(from_attributes=True)


class Entity(EntityInDB):
    """Schema returned by the API for entity data with nested relations.

    Includes category, entity_type, characteristics, locations, and sources.
    """

    # Nested relations - Pydantic will serialize these from SQLAlchemy models
    category: dict = Field(
        default={},
        title="Category",
        description="Category information",
        examples=[{"id": 1, "name": "Deity"}],
    )
    entity_type: dict = Field(
        default={},
        title="Entity Type",
        description="Entity type information",
        examples=[{"id": 2, "name": "Egyptian"}],
    )
    characteristics: list[dict] = Field(
        default=[],
        title="Characteristics",
        description="List of characteristics",
        examples=[[{"id": 1, "name": "Immortal", "value": "Yes"}]],
    )
    locations: list[dict] = Field(
        default=[],
        title="Locations",
        description="List of associated locations",
        examples=[[{"id": 1, "name": "Duat"}]],
    )
    sources: list[dict] = Field(
        default=[],
        title="Sources",
        description="List of mythological sources",
        examples=[[{"id": 1, "name": "Book of the Dead"}]],
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("category", "entity_type", mode="before")
    @classmethod
    def convert_model_to_dict(cls, v):
        if hasattr(v, "__tablename__"):  # SQLAlchemy model
            return {c.name: getattr(v, c.name) for c in v.__table__.columns}
        return v

    @field_validator("characteristics", "locations", "sources", mode="before")
    @classmethod
    def convert_list_to_dicts(cls, v):
        if v and hasattr(v[0], "__tablename__"):  # List of SQLAlchemy models
            return [
                {c.name: getattr(item, c.name) for c in v[0].__table__.columns}
                for item in v
            ]
        return v or []
