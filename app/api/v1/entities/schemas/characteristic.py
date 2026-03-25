from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.entities.enums import CharacteristicType


class CharacteristicBase(BaseModel):
    type: CharacteristicType
    description: str = Field(..., min_length=1, max_length=1000)


class CharacteristicCreate(CharacteristicBase):
    entity_id: int | None = None


class CharacteristicUpdate(BaseModel):
    type: CharacteristicType | None = None
    description: str | None = None


class CharacteristicInDB(CharacteristicBase):
    id: int
    entity_id: int
    model_config = ConfigDict(from_attributes=True)


class Characteristic(CharacteristicInDB):
    pass
