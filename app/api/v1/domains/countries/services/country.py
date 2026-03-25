from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.common.services import CRUDBaseService
from app.api.v1.domains.countries.models.country import Country
from app.api.v1.domains.countries.schemas.country import CountryCreate, CountryUpdate


class CountryService(CRUDBaseService[Country, CountryCreate, CountryUpdate]):
    """Service for Country CRUD operations."""

    def create(self, db: Session, *, obj_in: CountryCreate) -> Country:
        """Create a new country."""
        db_obj = Country(name=obj_in.name, status=obj_in.status)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Country,
        obj_in: Union[CountryUpdate, Dict[str, Any]],
    ) -> Country:
        """Update a country."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_multi(
        self, db: Session, *, relations: Optional[List[str]] = None
    ) -> List[Country]:
        """Get multiple countries with optional relations."""
        stmt = select(Country)
        if relations:
            stmt = stmt.options(*[selectinload(getattr(Country, r)) for r in relations])
        return db.execute(stmt).scalars().all()


country = CountryService(Country)
