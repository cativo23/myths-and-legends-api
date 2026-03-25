from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.api.v1.entities.enums import SourceType

if TYPE_CHECKING:
    from app.api.v1.entities.models.entity import Entity


class Source(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[SourceType] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    entity: Mapped["Entity"] = relationship("Entity", back_populates="sources")

    __table_args__ = (Index("ix_source_entity_type", "entity_id", "source_type"),)
