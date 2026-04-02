from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.entities.enums import CategoryName


class CategoryBase(BaseModel):
    """Base category properties.

    Categories classify entities by their nature (e.g., Deity, Creature, Place, Object).
    """

    name: CategoryName = Field(
        ...,
        title="Name",
        description="Category name",
        examples=["Deity", "Creature", "Place", "Object", "Event"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of the category",
        examples=["Divine beings and gods"],
    )


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""

    name: CategoryName | None = Field(
        None,
        title="Name",
        description="Category name",
        examples=["Deity"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of the category",
        examples=["Divine beings and gods"],
    )


class CategoryInDB(CategoryBase):
    """Base schema for category data stored in database."""

    id: int = Field(
        ...,
        title="ID",
        description="Unique category identifier",
        examples=[1],
    )
    model_config = ConfigDict(from_attributes=True)


class Category(CategoryInDB):
    """Schema returned by the API for category data."""

    entity_count: int = Field(
        default=0,
        title="Entity Count",
        description="Number of entities in this category",
        examples=[42],
    )
