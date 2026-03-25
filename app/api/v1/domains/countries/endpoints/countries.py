from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Path, Body
from sqlalchemy.orm import Session

from app.api.v1.domains.countries.schemas.country import (
    CountryCreate,
    CountryUpdate,
    Country as CountrySchema,
)
from app.api.v1.domains.countries.services.country import country as country_service
from app.api.v1.shared.deps import get_db

router = APIRouter()


@router.get("/", response_model=list[CountrySchema])
async def list_countries(
    *,
    db: Session = Depends(get_db),
    relations: str | None = None,
    sort: str = "name",
    order: str = "asc",
) -> list[CountrySchema]:
    """
    Lists all countries.

    **Query Parameters:**
    - `relations`: Comma-separated list of relations to include
    - `sort`: Field to sort by (name, id, created_at)
    - `order`: Sort order (asc, desc)
    """
    relations = [r.strip() for r in relations.split(",") if r.strip()] if relations else []
    all_countries = country_service.get_multi(db, relations=relations)

    # Sort results
    if order.lower() == "desc":
        return sorted(all_countries, key=lambda x: getattr(x, sort, x.id), reverse=True)
    return sorted(all_countries, key=lambda x: getattr(x, sort, x.id))


@router.post("/", response_model=CountrySchema, status_code=201)
async def add_country(
    db: Session = Depends(get_db),
    country: CountryCreate = Body(...),
) -> CountrySchema:
    """
    Add a Country.
    """
    country_created = country_service.create(db, obj_in=country)
    return country_created


@router.get("/{country_id}", response_model=CountrySchema)
async def get_country(
    *,
    db: Session = Depends(get_db),
    country_id: int,
    relations: str | None = None,
) -> CountrySchema:
    relations = [r.strip() for r in relations.split(",") if r.strip()] if relations else []
    country = country_service.get(db, item_id=country_id, relations=relations)

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.put("/{country_id}", response_model=CountrySchema)
async def update_country(
    *,
    db: Session = Depends(get_db),
    country_id: int,
    country_in: CountryUpdate,
) -> CountrySchema:
    """
    Update a country.
    """
    country = country_service.get(db, item_id=country_id)

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    country = country_service.update(db, db_obj=country, obj_in=country_in)
    return country


@router.delete("/{country_id}", status_code=204)
async def delete_country(
    *,
    db: Session = Depends(get_db),
    country_id: int,
) -> None:
    """
    Delete a country.
    """
    country = country_service.get(db, item_id=country_id)

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    country_service.remove(db, item_id=country_id)
