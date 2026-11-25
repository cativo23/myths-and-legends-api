from typing import Annotated, Any, List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.params import Path, Body
from sqlalchemy.orm import Session

from app.api.common.sorting import SortOrder
from app.api.v1.domains.countries.schemas.country import (
    CountryCreate,
    CountryUpdate,
    Country as CountrySchema,
)
from app.api.v1.domains.countries.services.country import country as country_service
from app.api.v1.shared.deps import get_db, get_current_active_superuser
from app.api.v1.domains.users.models.user import User as UserModel

router = APIRouter()


@router.get(
    "/",
    response_model=List[CountrySchema],
    summary="List Countries",
    description="Retrieve a list of all countries in the system.",
    responses={
        200: {"description": "Successful retrieval of countries"},
    },
)
def list_countries(
    *,
    db: Session = Depends(get_db),
    sort: Annotated[
        Literal["name", "id"],
        Query(description="Field to sort by", examples=["name", "id"]),
    ] = "name",
    order: Annotated[
        SortOrder, Query(description="Sort order", examples=["asc", "desc"])
    ] = "asc",
) -> List[CountrySchema]:
    """List all countries with optional sorting."""
    return country_service.get_multi(db, sort=sort, order=order)


@router.post(
    "/",
    response_model=CountrySchema,
    status_code=201,
    summary="Create Country",
    description="Create a new country in the system. Requires superuser privileges.",
    responses={
        201: {"description": "Country successfully created"},
        400: {"description": "Invalid input data"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def add_country(
    db: Session = Depends(get_db),
    country: CountryCreate = Body(
        ...,
        description="Country data to create",
        examples=[{"name": "Nigeria", "status": True}],
    ),
    current_user: UserModel = Depends(get_current_active_superuser),
) -> CountrySchema:
    """Create a new country. Requires superuser privileges."""
    country_created = country_service.create(db, obj_in=country)
    return country_created


@router.get(
    "/{country_id}",
    response_model=CountrySchema,
    summary="Get Country",
    description="Retrieve a specific country by its ID.",
    responses={
        200: {"description": "Successful retrieval of country"},
        404: {"description": "Country not found"},
    },
)
def get_country(
    *,
    db: Session = Depends(get_db),
    country_id: int = Path(..., description="Country ID", examples=[1], gt=0),
) -> CountrySchema:
    """Get a country by ID."""
    country = country_service.get(db, item_id=country_id)

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.put(
    "/{country_id}",
    response_model=CountrySchema,
    summary="Update Country",
    description="Update an existing country by its ID. Requires superuser privileges.",
    responses={
        200: {"description": "Country successfully updated"},
        404: {"description": "Country not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def update_country(
    *,
    db: Session = Depends(get_db),
    country_id: int = Path(..., description="Country ID", examples=[1], gt=0),
    country_in: CountryUpdate = Body(..., description="Updated country data"),
    current_user: UserModel = Depends(get_current_active_superuser),
) -> CountrySchema:
    """Update a country. Requires superuser privileges."""
    country = country_service.get(db, item_id=country_id)

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    country = country_service.update(db, db_obj=country, obj_in=country_in)
    return country


@router.delete(
    "/{country_id}",
    status_code=204,
    summary="Delete Country",
    description="Delete a country by its ID. Requires superuser privileges.",
    responses={
        204: {"description": "Country successfully deleted"},
        404: {"description": "Country not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def delete_country(
    *,
    db: Session = Depends(get_db),
    country_id: int = Path(..., description="Country ID", examples=[1], gt=0),
    current_user: UserModel = Depends(get_current_active_superuser),
) -> None:
    """Delete a country. Requires superuser privileges."""
    country = country_service.get(db, item_id=country_id)

    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    country_service.remove(db, item_id=country_id)
