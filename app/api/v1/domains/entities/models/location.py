from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.api.v1.domains.entities.models.entity import Entity


class Location(Base):
    __tablename__ = "location"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    municipality: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    place_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    entity: Mapped["Entity"] = relationship("Entity", back_populates="locations")
