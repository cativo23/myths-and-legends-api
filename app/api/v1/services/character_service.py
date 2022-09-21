from typing import Any, Dict, Optional, Union

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.common.services import CRUDBaseService
from .country_service import country as country_service
from ..models import Character
from ..schemas import CharacterCreate, CharacterUpdate


class CharacterService(CRUDBaseService[Character, CharacterCreate, CharacterUpdate]):

    def search(self, db: Session, *, term: str) -> Any:
        """
            Search characters by name.
        """
        return db.query(self.model).filter(self.model.name.ilike(f"%{term}%")).all()

    def create(self, db: Session, *, obj_in: CharacterCreate) -> Character:

        self.validate_country(db, obj_in.country_id)

        existing_character = self.get_by_name(db, name=obj_in.name)

        if existing_character:
            raise HTTPException(
                status_code=422,
                detail="Character already exists",
            )

        return super().create(db, obj_in=obj_in)

    def update(
            self, db: Session, *, db_obj: Character, obj_in: Union[CharacterUpdate, Dict[str, Any]]
    ) -> Character:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        existing_character = self.get_by_name(db, name=obj_in.name, exclude=db_obj.id)

        if existing_character:
            raise HTTPException(
                status_code=422,
                detail="Character already exists",
            )

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_by_name(self, db, name: str, exclude: int = None) -> Optional[Character]:
        """
         Get for a character by name.
         """
        if exclude:
            return db.query(self.model).filter(self.model.name == name).filter(self.model.id != exclude).first()

        return db.query(self.model).filter(self.model.name == name).first()

    @staticmethod
    def validate_country(db, country_id: int):
        country = country_service.validate_existence(db, item_id=country_id)

        if not country:
            raise HTTPException(
                status_code=422,
                detail="Country does not exist",
            )

        if not country.status:
            raise HTTPException(
                status_code=422,
                detail="Country is inactive",
            )


character = CharacterService(Character)
