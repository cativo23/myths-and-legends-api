from sqlalchemy.orm import Session

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.domains.entities.models.source import Source
from app.api.v1.domains.entities.schemas.source import SourceCreate, SourceUpdate


class SourceService(CRUDBaseService[Source, SourceCreate, SourceUpdate]):
    """Service for Source CRUD operations."""

    def get_by_entity(self, db: Session, *, entity_id: int) -> list[Source]:
        """Get all sources for an entity"""
        return db.query(self.model).filter(self.model.entity_id == entity_id).all()
