from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.api.common.services import CRUDBaseService
from ..models import Country
from ..schemas import CountryCreate, CountryUpdate


class CountryService(CRUDBaseService[Country, CountryCreate, CountryUpdate]):

    def create(self, db: Session, *, obj_in: CountryCreate) -> Country:
        db_obj = Country(
            name=obj_in.name,
            status=obj_in.status
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Country, obj_in: Union[CountryUpdate, Dict[str, Any]]
    ) -> Country:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data)


country = CountryService(Country)
