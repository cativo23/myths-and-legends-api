from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.entities.enums import SourceType


class SourceBase(BaseModel):
    """Base source properties.

    Sources reference the original materials where myths and legends
    were documented (books, manuscripts, websites, oral traditions).
    """

    source_type: SourceType = Field(
        ...,
        title="Source Type",
        description="Type of source (e.g., Book, Website, Manuscript, Oral Tradition)",
        examples=["Book", "Website", "Manuscript", "Oral Tradition"],
    )
    title: str = Field(
        ...,
        title="Title",
        description="Title of the source",
        min_length=1,
        max_length=255,
        examples=["The Book of the Dead", "Popol Vuh"],
    )
    author: str | None = Field(
        None,
        title="Author",
        description="Author or creator of the source",
        max_length=255,
        examples=["Anonymous", "James George Frazer"],
    )
    url: str | None = Field(
        None,
        title="URL",
        description="URL where the source can be accessed",
        max_length=500,
        examples=["https://example.com/book-of-the-dead"],
    )


class SourceCreate(SourceBase):
    """Schema for creating a new source."""

    entity_id: int | None = Field(
        None,
        title="Entity ID",
        description="ID of the associated entity",
        examples=[1],
    )


class SourceUpdate(BaseModel):
    """Schema for updating an existing source."""

    source_type: SourceType | None = Field(
        None,
        title="Source Type",
        description="Type of source",
        examples=["Book"],
    )
    title: str | None = Field(
        None,
        title="Title",
        description="Title of the source",
        min_length=1,
        max_length=255,
        examples=["The Book of the Dead"],
    )
    author: str | None = Field(
        None,
        title="Author",
        description="Author or creator of the source",
        max_length=255,
        examples=["Anonymous"],
    )
    url: str | None = Field(
        None,
        title="URL",
        description="URL where the source can be accessed",
        max_length=500,
        examples=["https://example.com/book-of-the-dead"],
    )


class SourceInDB(SourceBase):
    """Base schema for source data stored in database."""

    id: int = Field(
        ...,
        title="ID",
        description="Unique source identifier",
        examples=[1],
    )
    entity_id: int = Field(
        ...,
        title="Entity ID",
        description="ID of the associated entity",
        examples=[1],
    )
    model_config = ConfigDict(from_attributes=True)


class Source(SourceInDB):
    """Schema returned by the API for source data."""

    pass
