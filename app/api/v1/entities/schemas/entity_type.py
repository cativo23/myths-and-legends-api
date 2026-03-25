from pydantic import BaseModel, ConfigDict

from app.api.v1.entities.enums import EntityTypeName


class EntityTypeBase(BaseModel):
    name: EntityTypeName
    description: str | None = None


class EntityTypeCreate(EntityTypeBase):
    pass


class EntityTypeUpdate(BaseModel):
    name: EntityTypeName | None = None
    description: str | None = None


class EntityTypeInDB(EntityTypeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EntityType(EntityTypeInDB):
    entity_count: int = 0
