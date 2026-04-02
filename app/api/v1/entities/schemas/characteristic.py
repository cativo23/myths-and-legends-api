from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.entities.enums import CharacteristicType


class CharacteristicBase(BaseModel):
    """Base characteristic properties.

    Characteristics describe specific traits or attributes of entities
    (e.g., powers, weaknesses, physical features).
    """

    type: CharacteristicType = Field(
        ...,
        title="Type",
        description="Type of characteristic (e.g., Power, Weakness, Physical Feature)",
        examples=["Power", "Weakness", "Physical Feature", "Ability"],
    )
    description: str = Field(
        ...,
        title="Description",
        description="Description of the characteristic",
        min_length=1,
        max_length=1000,
        examples=["Can control the winds and summon storms"],
    )


class CharacteristicCreate(CharacteristicBase):
    """Schema for creating a new characteristic."""

    entity_id: int | None = Field(
        None,
        title="Entity ID",
        description="ID of the associated entity",
        examples=[1],
    )


class CharacteristicUpdate(BaseModel):
    """Schema for updating an existing characteristic."""

    type: CharacteristicType | None = Field(
        None,
        title="Type",
        description="Type of characteristic",
        examples=["Power"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of the characteristic",
        min_length=1,
        max_length=1000,
        examples=["Can control the winds"],
    )


class CharacteristicInDB(CharacteristicBase):
    """Base schema for characteristic data stored in database."""

    id: int = Field(
        ...,
        title="ID",
        description="Unique characteristic identifier",
        examples=[1],
    )
    entity_id: int = Field(
        ...,
        title="Entity ID",
        description="ID of the associated entity",
        examples=[1],
    )
    model_config = ConfigDict(from_attributes=True)


class Characteristic(CharacteristicInDB):
    """Schema returned by the API for characteristic data."""

    pass
