from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Path, Body
from sqlalchemy.orm import Session

from app.api import deps
from ..models import Country
from ..schemas import CountryCreate, CountryUpdate, Country as CountrySchema
from ..services import country as country_service
from app.core.config import settings

router = APIRouter()
fakeDatabase = {
    1: {'name': 'El Salvador', 'status': True},
    2: {'name': 'Guatemala', 'status': True},
    3: {'name': 'Honduras', 'status': True},
    4: {'name': 'Nicaragua', 'status': True},
    5: {'name': 'Costa Rica', 'status': True},
    6: {'name': 'Panama', 'status': True},
}


@router.get("/")
def list_countries(
        db: Session = Depends(deps.get_db),
):
    all_countries = db.query(Country).all()
    return all_countries


@router.post("/")
def add_country(
        db: Session = Depends(deps.get_db),
        country: CountryCreate = Body(...),
):
    item = Country(name=country.name, status=country.status)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{country_id}")
def get_country(db: Session = Depends(deps.get_db), country_id: int = Path(...)) -> CountrySchema:
    country = country_service.get(db, id=country_id)
    return country


@router.put("/{country_id}", response_model=CountrySchema)
def update_country(*,
                   db: Session = Depends(deps.get_db),
                   country_id: int,
                   country_in: CountryUpdate
                   ) -> CountrySchema:
    """
    Update a country.
    """
    country = country_service.get(db, id=country_id)
    if not country:
        raise HTTPException(
            status_code=404,
            detail="The Country with this id does not exist in the system.",
        )
    country = country_service.update(db, db_obj=country, obj_in=country_in)
    return country


@router.delete("/{country_id}", response_model=Any)
def delete_country(*,
                   db: Session = Depends(deps.get_db),
                   country_id: int
                   ) -> Any:
    """
    Update a country.
    """
    country = country_service.get(db, id=country_id)
    if not country:
        raise HTTPException(
            status_code=404,
            detail="The Country with this id does not exist in the system.",
        )

    country = country_service.remove(db, id=country_id)

    return {
        "message": "Country deleted successfully"
    }
