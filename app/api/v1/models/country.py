from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .character import Character  # noqa: F401


class Country(Base):
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[bool] = mapped_column(Boolean(), default=True)
    characters: Mapped[Optional[List["Character"]]] = relationship("Character", back_populates="country", lazy="noload")
