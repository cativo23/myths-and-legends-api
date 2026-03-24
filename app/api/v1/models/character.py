from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, DateTime, Enum as EnumType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..enums import CharacterType, Gender
from ....db.base_class import Base

if TYPE_CHECKING:
    from .country import Country  # noqa: F401


class Character(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, index=True, unique=True, nullable=True)
    type: Mapped[CharacterType] = mapped_column(EnumType(CharacterType), default=CharacterType.human)
    gender: Mapped[Gender] = mapped_column(EnumType(Gender), default=Gender.female)
    image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    description: Mapped[Optional[str]] = mapped_column(String, default="", nullable=True)
    country_id: Mapped[Optional[int]] = mapped_column(ForeignKey("country.id"), nullable=True)
    country: Mapped[Optional["Country"]] = relationship("Country", back_populates="characters", lazy="noload")
