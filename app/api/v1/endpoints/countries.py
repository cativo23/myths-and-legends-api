from typing import Any

from fastapi import APIRouter, Depends
from fastapi.params import Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..schemas import CountryCreate, CountryUpdate, Country as CountrySchema
from ..services import country as country_service
from ...common.pagination.json_api_page import JsonApiPage
from ...common.responses import not_found, found, updated, created, deleted
from ....api import deps

router = APIRouter()


@router.get("/", response_model=JsonApiPage[CountrySchema])
def list_countries(
        *,
        db: Session = Depends(deps.get_db),
) -> Any:
    """
        Lists all countries.
    """
    all_countries = country_service.get_all(db)
    return all_countries


@router.post("/")
def add_country(
        db: Session = Depends(deps.get_db),
        country: CountryCreate = Body(...),
):
    """
        Add a Country.
    """
    country_created = country_service.create(db, obj_in=country)

    return created(obj_name="Country", obj=country_created)


@router.get("/{country_id}")
def get_country(db: Session = Depends(deps.get_db), country_id: int = Path(...)) -> JSONResponse:
    country = country_service.get(db, item_id=country_id)

    if not country:
        return not_found(obj_name="Country")

    return found(obj_name="Country", obj=country)


@router.put("/{country_id}", response_model=CountrySchema)
def update_country(*,
                   db: Session = Depends(deps.get_db),
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
                   db: Session = Depends(deps.get_db),
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
