from fastapi import APIRouter, Depends
from fastapi.params import Body
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1 import models
from app.api.v1.schemas.country import CountryCreate
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


@router.post("/")
def add_country(
        db: Session = Depends(deps.get_db),
        country: CountryCreate = Body(...),
):
    item = models.Country(name=country.name, status=country.status)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{id}")
def get_country(id: int) -> dict:
    return fakeDatabase[id]
