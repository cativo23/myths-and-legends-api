from datetime import datetime
from enum import Enum

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum as EnumType
from sqlalchemy.orm import relationship

from ..enums import CharacterType, Gender
from ....db.base_class import Base


class Character(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(EnumType(CharacterType), default=CharacterType.human)
    gender = Column(EnumType(Gender), default=Gender.female)
    image = Column(String)
    created = Column(DateTime, default=datetime.utcnow)
    description = Column(String, default="")
    country_id = Column(Integer, ForeignKey("country.id"))
    country = relationship("Country", back_populates="characters")
