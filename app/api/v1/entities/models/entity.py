from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, ARRAY, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.api.v1.entities.models.category import Category
    from app.api.v1.entities.models.entity_type import EntityType
    from app.api.v1.entities.models.characteristic import Characteristic
    from app.api.v1.entities.models.location import Location
    from app.api.v1.entities.models.source import Source
    from app.api.v1.entities.models.entity_relation import EntityRelation


class Entity(Base):
    __tablename__ = "entity"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alternative_names: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id"), nullable=False, index=True
    )
    entity_type_id: Mapped[int] = mapped_column(
        ForeignKey("entity_type.id"), nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    origin: Mapped[str | None] = mapped_column(Text, nullable=True)
    behavior: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="entities")
    entity_type: Mapped["EntityType"] = relationship(
        "EntityType", back_populates="entities"
    )
    characteristics: Mapped[list["Characteristic"]] = relationship(
        "Characteristic", back_populates="entity", cascade="all, delete-orphan"
    )
    locations: Mapped[list["Location"]] = relationship(
        "Location", back_populates="entity", cascade="all, delete-orphan"
    )
    sources: Mapped[list["Source"]] = relationship(
        "Source", back_populates="entity", cascade="all, delete-orphan"
    )
    relations_as_origin: Mapped[list["EntityRelation"]] = relationship(
        "EntityRelation",
        foreign_keys="EntityRelation.entity_origin_id",
        back_populates="entity_origin",
    )
    relations_as_destination: Mapped[list["EntityRelation"]] = relationship(
        "EntityRelation",
        foreign_keys="EntityRelation.entity_destination_id",
        back_populates="entity_destination",
    )

    # Indexes
    __table_args__ = (
        Index("ix_entity_category_type", "category_id", "entity_type_id"),
        Index("ix_entity_active", "is_active", "name"),
    )
