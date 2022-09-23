from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Shared properties
class CountryBase(BaseModel):
    name: Optional[str] = None
    status: Optional[bool] = True


# Properties to receive via API on creation
class CountryCreate(CountryBase):
    name: str = Field(..., title="Country Name", max_length=100, example="Nigeria")
    status: Optional[bool] = Field(True, title="Country Status", example=True)


# Properties to receive via API on update
class CountryUpdate(CountryBase):
    name: Optional[str] = None
    status: Optional[bool] = True


class CountryInDBBase(CountryBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class Country(CountryInDBBase):
    characters: Optional[list]
    pass

