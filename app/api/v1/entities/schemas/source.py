from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.entities.enums import SourceType


class SourceBase(BaseModel):
    source_type: SourceType
    title: str = Field(..., min_length=1, max_length=255)
    author: str | None = Field(None, max_length=255)
    url: str | None = Field(None, max_length=500)


class SourceCreate(SourceBase):
    entity_id: int | None = None


class SourceUpdate(BaseModel):
    source_type: SourceType | None = None
    title: str | None = None
    author: str | None = None
    url: str | None = None


class SourceInDB(SourceBase):
    id: int
    entity_id: int
    model_config = ConfigDict(from_attributes=True)


class Source(SourceInDB):
    pass
