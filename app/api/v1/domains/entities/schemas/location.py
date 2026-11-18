from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    """Base location properties.

    Locations represent geographical places associated with entities
    (e.g., where a mythological creature is said to appear).
    """

    department: str = Field(
        ...,
        title="Department",
        description="Department or state",
        min_length=1,
        max_length=100,
        examples=["Cundinamarca", "Oaxaca"],
    )
    municipality: str | None = Field(
        None,
        title="Municipality",
        description="Municipality or city",
        max_length=100,
        examples=["Bogotá", "Tlacolula"],
    )
    place_description: str | None = Field(
        None,
        title="Place Description",
        description="Description of the specific place",
        examples=["Ancient temple ruins near the mountain"],
        max_length=1000,
    )


class LocationCreate(LocationBase):
    """Schema for creating a new location."""

    entity_id: int = Field(
        ...,
        title="Entity ID",
        description="ID of the associated entity",
        examples=[1],
    )


class LocationUpdate(BaseModel):
    """Schema for updating an existing location."""

    department: str | None = Field(
        None,
        title="Department",
        description="Department or state",
        min_length=1,
        max_length=100,
        examples=["Cundinamarca"],
    )
    municipality: str | None = Field(
        None,
        title="Municipality",
        description="Municipality or city",
        max_length=100,
        examples=["Bogotá"],
    )
    place_description: str | None = Field(
        None,
        title="Place Description",
        description="Description of the specific place",
        max_length=1000,
        examples=["Ancient temple ruins"],
    )


class LocationInDB(LocationBase):
    """Base schema for location data stored in database."""

    id: int = Field(
        ...,
        title="ID",
        description="Unique location identifier",
        examples=[1],
    )
    entity_id: int = Field(
        ...,
        title="Entity ID",
        description="ID of the associated entity",
        examples=[1],
    )
    model_config = ConfigDict(from_attributes=True)


class Location(LocationInDB):
    """Schema returned by the API for location data."""

    pass
