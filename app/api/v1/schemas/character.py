from datetime import datetime as datetime_type
from typing import Optional

from pydantic import BaseModel, Field

from app.api.v1.enums import CharacterType, Gender


# Shared properties
class CharacterBase(BaseModel):
    name: Optional[str] = None
    type: CharacterType = CharacterType.human


# Properties to receive via API on creation
class CharacterCreate(CharacterBase):
    name: str = Field(..., title="Character Name", max_length=100, example="Cipitio")
    type: CharacterType = Field(CharacterType.human, title="Character type", example=CharacterType.human)
    gender: Gender = Field(Gender.female, title="Character Gender", example=Gender.female)
    image: str = Field(None, title="Characters Image", example="Siguanaba")
    description: str = Field(..., max_length=5000, example="Lorem Ipsum")
    country_id: int = Field(..., title="Country of this character", example=1)


# Properties to receive via API on update
class CharacterUpdate(CharacterBase):
    name: Optional[str] = Field(None, title="Character Name", max_length=100, example="Cipitio")
    type: Optional[CharacterType] = Field(CharacterType.human, title="Character type", example=CharacterType.human)
    gender: Optional[Gender] = Field(Gender.female, title="Character Gender", example=Gender.female)
    image: Optional[str] = Field(None, title="Characters Image", example="Siguanaba")
    description: Optional[str] = Field("", max_length=5000, example="Lorem Ipsum")


class CharacterInDBBase(CharacterBase):
    id: Optional[int] = None
    created_at: datetime_type = Field(datetime_type.now(), title="When the Character was created in DB")

    class Config:
        orm_mode = True


# Additional properties to return via API
class Character(CharacterInDBBase):
    pass
