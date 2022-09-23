from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as EnumType
from sqlalchemy.orm import relationship

from ..enums import CharacterType, Gender
from ....db.base_class import Base

if TYPE_CHECKING:
    from .country import Country  # noqa: F401


class Character(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    type = Column(EnumType(CharacterType), default=CharacterType.human)
    gender = Column(EnumType(Gender), default=Gender.female)
    image = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(String, default="")
    country_id = Column(Integer, ForeignKey("country.id"))
    country = relationship("Country", back_populates="characters", lazy="noload")
