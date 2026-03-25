from sqlalchemy.orm import Session

from app.api.common.services.base_service import CRUDBaseService
from app.api.v1.entities.models.characteristic import Characteristic
from app.api.v1.entities.schemas.characteristic import CharacteristicCreate, CharacteristicUpdate


class CharacteristicService(CRUDBaseService[Characteristic, CharacteristicCreate, CharacteristicUpdate]):
    def __init__(self):
        super().__init__(Characteristic)

    def get_by_entity(self, db: Session, *, entity_id: int) -> list[Characteristic]:
        """Get all characteristics for an entity"""
        return db.query(self.model).filter(self.model.entity_id == entity_id).all()
