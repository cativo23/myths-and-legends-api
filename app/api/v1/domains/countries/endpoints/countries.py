from typing import Any

from fastapi import APIRouter, Depends
from fastapi.params import Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.domains.countries.schemas.country import CountryCreate, CountryUpdate, Country as CountrySchema
from app.api.v1.domains.countries.services.country import country as country_service
from app.api.common.responses import not_found, found, updated, created, deleted
from app.api.v1.shared.deps import get_db

router = APIRouter()


@router.get("/", response_model=list[CountrySchema])
def list_countries(
        *,
        db: Session = Depends(get_db),
        relations: str = None,
) -> Any:
    """
        Lists all countries.
    """
    relations = relations.split(',') if relations else []
    all_countries = country_service.get_multi(db, relations=relations)
    return found(obj_name="Countries", obj=all_countries)


@router.post("/")
def add_country(
        db: Session = Depends(get_db),
        country: CountryCreate = Body(...),
):
    """
        Add a Country.
    """
    country_created = country_service.create(db, obj_in=country)

    return created(obj_name="Country", obj=country_created)


@router.get("/{country_id}")
def get_country(
        db: Session = Depends(get_db),
        country_id: int = Path(...),
        relations: str = None,
) -> JSONResponse:
    relations = relations.split(',') if relations else []

    country = country_service.get(db, item_id=country_id, relations=relations)

    if not country:
        return not_found(obj_name="Country")

    return found(obj_name="Country", obj=country)


@router.put("/{country_id}", response_model=CountrySchema)
def update_country(*,
                   db: Session = Depends(get_db),
                   country_id: int,
                   country_in: CountryUpdate
                   ) -> JSONResponse:
    """
    Update a country.
    """
    country = country_service.get(db, item_id=country_id)

    if not country:
        return not_found(obj_name="Country")

    country = country_service.update(db, db_obj=country, obj_in=country_in)

    return updated(obj_name="Country", obj=country)


@router.delete("/{country_id}", response_model=Any)
def delete_country(*,
                   db: Session = Depends(get_db),
                   country_id: int
                   ) -> Any:
    """
    Delete a country.
    """
    country = country_service.get(db, item_id=country_id)

    if not country:
        return not_found(obj_name="Country")

    country_service.remove(db, item_id=country_id)

    return deleted(obj_name="Country")
