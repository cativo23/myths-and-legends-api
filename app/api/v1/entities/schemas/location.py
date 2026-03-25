from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    department: str = Field(..., min_length=1, max_length=100)
    municipality: str | None = Field(None, max_length=100)
    place_description: str | None = None


class LocationCreate(LocationBase):
    entity_id: int | None = None


class LocationUpdate(BaseModel):
    department: str | None = None
    municipality: str | None = None
    place_description: str | None = None


class LocationInDB(LocationBase):
    id: int
    entity_id: int
    model_config = ConfigDict(from_attributes=True)


class Location(LocationInDB):
    pass
