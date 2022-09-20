from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.api.v1.enums import CharacterType, Gender


# Shared properties
class CharacterBase(BaseModel):
    name: Optional[str] = None
    status: Optional[bool] = True


# Properties to receive via API on creation
class CharacterCreate(CharacterBase):
    name: str = Field(None, title="Character Name", max_length=100, example="Cipitio")
    type: Optional[CharacterType] = Field(CharacterType.human, title="Character type", example=CharacterType.human)
    gender: Optional[Gender] = Field(Gender.female, title="Character Gender", example=Gender.female)
    image: Optional[str] = Field(None, title="Characters Image", example="Siguanaba")


# Properties to receive via API on update
class CharacterUpdate(CharacterBase):
    name: Optional[str] = None
    status: Optional[bool] = True


class CharacterInDBBase(CharacterBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class Character(CharacterInDBBase):
    pass

