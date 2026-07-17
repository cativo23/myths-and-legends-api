from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.api.v1.domains.entities.enums import CharacteristicType

if TYPE_CHECKING:
    from app.api.v1.domains.entities.models.entity import Entity


class Characteristic(Base):
    __tablename__ = "characteristic"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[CharacteristicType] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    entity: Mapped["Entity"] = relationship("Entity", back_populates="characteristics")

    __table_args__ = (Index("ix_characteristic_entity_type", "entity_id", "type"),)
