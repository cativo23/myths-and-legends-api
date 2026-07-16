from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, Query, HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import location
from app.api.v1.entities.models.location import Location
from app.api.v1.entities.schemas.location import Location as LocationSchema

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "/",
    response_model=Page[LocationSchema],
    summary="List Locations",
    description="Retrieve a paginated list of locations, optionally filtered by department.",
    responses={
        200: {"description": "Successful retrieval of locations"},
    },
)
async def list_locations(
    db: Annotated[Session, Depends(get_db)],
    department: Annotated[
        str | None,
        Query(
            max_length=200,
            description="Filter by department",
            examples=["Cundinamarca", "Oaxaca"],
        ),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
):
    """List all locations, optionally filtered by department, paginated at the database level."""
    stmt = select(Location)
    if department:
        stmt = stmt.where(Location.department.ilike(f"%{department}%"))
    stmt = stmt.order_by(Location.id)
    return paginate(db, stmt, Params(page=page, size=size))


@router.get(
    "/{id:int}",
    response_model=LocationSchema,
    summary="Get Location",
    description="Retrieve a specific location by ID.",
    responses={
        200: {"description": "Successful retrieval of location"},
        404: {"description": "Location not found"},
    },
)
async def get_location(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Location ID", examples=[1])],
):
    """Get location by ID."""
    db_location = location.get(db, item_id=id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location


@router.get(
    "/{department}",
    response_model=List[LocationSchema],
    summary="Get Locations by Department",
    description="Retrieve all locations in a specific department.",
    responses={
        200: {"description": "Successful retrieval of locations"},
    },
)
async def get_location_by_department(
    db: Annotated[Session, Depends(get_db)],
    department: Annotated[
        str,
        Path(max_length=200, description="Department name", examples=["Cundinamarca"]),
    ],
):
    """Get all locations in a specific department."""
    return location.get_by_department(db, department=department)
