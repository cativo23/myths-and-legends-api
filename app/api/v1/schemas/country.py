from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class CountryBase(BaseModel):
    name: Optional[str] = None
    status: Optional[bool] = True


# Properties to receive via API on creation
class CountryCreate(CountryBase):
    name: str
    status: bool


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
    pass

