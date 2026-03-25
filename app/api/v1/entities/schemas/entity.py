from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    alternative_names: list[str] | None = None
    category_id: int
    entity_type_id: int
    description: str | None = None
    origin: str | None = None
    behavior: str | None = None
    image_url: str | None = Field(None, max_length=500)
    is_active: bool = True


class EntityCreate(EntityBase):
    """For creation - characteristics, locations, sources are handled separately"""
    pass


class EntityUpdate(BaseModel):
    """For updates - all fields optional"""

    name: str | None = Field(None, min_length=1, max_length=255)
    alternative_names: list[str] | None = None
    category_id: int | None = None
    entity_type_id: int | None = None
    description: str | None = None
    origin: str | None = None
    behavior: str | None = None
    image_url: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class EntityInDB(EntityBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Entity(EntityInDB):
    """Full response schema with nested relations"""
    # Nested relations - Pydantic will serialize these from SQLAlchemy models
    category: dict = {}
    entity_type: dict = {}
    characteristics: list[dict] = []
    locations: list[dict] = []
    sources: list[dict] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator('category', 'entity_type', mode='before')
    @classmethod
    def convert_model_to_dict(cls, v):
        if hasattr(v, '__tablename__'):  # SQLAlchemy model
            return {c.name: getattr(v, c.name) for c in v.__table__.columns}
        return v

    @field_validator('characteristics', 'locations', 'sources', mode='before')
    @classmethod
    def convert_list_to_dicts(cls, v):
        if v and hasattr(v[0], '__tablename__'):  # List of SQLAlchemy models
            return [{c.name: getattr(item, c.name) for c in v[0].__table__.columns} for item in v]
        return v or []
