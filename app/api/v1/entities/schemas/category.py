from pydantic import BaseModel, ConfigDict

from app.api.v1.entities.enums import CategoryName


class CategoryBase(BaseModel):
    name: CategoryName
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: CategoryName | None = None
    description: str | None = None


class CategoryInDB(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class Category(CategoryInDB):
    entity_count: int = 0
