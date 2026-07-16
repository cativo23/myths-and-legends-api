from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.api.v1.entities.enums import RelationType

if TYPE_CHECKING:
    from app.api.v1.entities.models.entity import Entity


class EntityRelation(Base):
    __tablename__ = "entity_relation"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_origin_id: Mapped[int] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), nullable=False
    )
    entity_destination_id: Mapped[int] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[RelationType] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    entity_origin: Mapped["Entity"] = relationship(
        "Entity",
        foreign_keys=[entity_origin_id],
        back_populates="relations_as_origin",
    )
    entity_destination: Mapped["Entity"] = relationship(
        "Entity",
        foreign_keys=[entity_destination_id],
        back_populates="relations_as_destination",
    )

    # Prevent duplicate relations between same entities
    __table_args__ = (
        UniqueConstraint(
            "entity_origin_id",
            "entity_destination_id",
            "relation_type",
            name="uq_entity_relation_unique",
        ),
        Index("ix_entity_relation_origin", "entity_origin_id"),
        Index("ix_entity_relation_destination", "entity_destination_id"),
    )
