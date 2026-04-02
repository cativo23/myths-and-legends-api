from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


# Shared properties
class CountryBase(BaseModel):
    """Base country properties shared across schemas."""

    name: Optional[str] = Field(
        None,
        title="Country Name",
        description="Official name of the country",
        examples=["Nigeria", "Mexico", "Japan"],
        max_length=100,
    )
    status: Optional[bool] = Field(
        True,
        title="Status",
        description="Whether the country is active in the system",
        examples=[True],
    )


# Properties to receive via API on creation
class CountryCreate(CountryBase):
    """Schema for creating a new country."""

    name: str = Field(
        ...,
        title="Country Name",
        description="Official name of the country (required)",
        min_length=1,
        max_length=100,
        examples=["Nigeria"],
    )
    status: Optional[bool] = Field(
        True,
        title="Status",
        description="Whether the country is active in the system",
        examples=[True],
    )


# Properties to receive via API on update
class CountryUpdate(CountryBase):
    """Schema for updating an existing country."""

    name: Optional[str] = Field(
        None,
        title="Country Name",
        description="New official name of the country",
        min_length=1,
        max_length=100,
        examples=["Nigeria"],
    )
    status: Optional[bool] = Field(
        None,
        title="Status",
        description="Whether the country is active in the system",
        examples=[True],
    )


class CountryInDBBase(CountryBase):
    """Base schema for country data stored in database."""

    id: Optional[int] = Field(
        None,
        title="ID",
        description="Unique country identifier",
        examples=[1],
    )

    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class Country(CountryInDBBase):
    """Schema returned by the API for country data."""

    pass
