from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.domains.entities.enums import CategoryName


class CategoryBase(BaseModel):
    """Base category properties.

    Categories classify entities as a MYTH, a LEGEND or a TRADITION.
    """

    name: CategoryName = Field(
        ...,
        title="Name",
        description="Category name",
        examples=["MYTH", "LEGEND", "TRADITION"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of the category",
        examples=["Stories told as having happened in a real place"],
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
        examples=["LEGEND"],
    )
    description: str | None = Field(
        None,
        title="Description",
        description="Description of the category",
        examples=["Stories told as having happened in a real place"],
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
