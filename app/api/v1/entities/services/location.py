from sqlalchemy.orm import Session

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.entities.models.location import Location
from app.api.v1.entities.schemas.location import LocationCreate, LocationUpdate


class LocationService(CRUDBaseService[Location, LocationCreate, LocationUpdate]):
    def __init__(self):
        super().__init__(Location)

    def get_by_entity(self, db: Session, *, entity_id: int) -> list[Location]:
        """Get all locations for an entity"""
        return db.query(self.model).filter(self.model.entity_id == entity_id).all()

    def get_by_department(self, db: Session, *, department: str) -> list[Location]:
        """Get all locations in a department"""
        return (
            db.query(self.model)
            .filter(Location.department.ilike(f"%{department}%"))
            .all()
        )
