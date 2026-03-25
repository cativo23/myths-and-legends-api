from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.api.v1.entities.enums import EntityTypeName

if TYPE_CHECKING:
    from app.api.v1.entities.models.entity import Entity


class EntityType(Base):
    __tablename__ = "entity_type"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[EntityTypeName] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    entities: Mapped[list["Entity"]] = relationship("Entity", back_populates="entity_type")
