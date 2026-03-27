from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import location
from app.api.v1.entities.models.location import Location
from app.api.v1.entities.schemas.location import Location as LocationSchema

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "/",
    response_model=List[LocationSchema],
    summary="List Locations",
    description="Retrieve all locations, optionally filtered by department.",
    responses={
        200: {"description": "Successful retrieval of locations"},
    },
)
async def list_locations(
    db: Annotated[Session, Depends(get_db)],
    department: Annotated[str | None, Query(description="Filter by department", examples=["Cundinamarca", "Oaxaca"])] = None,
):
    """List all locations, optionally filtered by department."""
    if department:
        return location.get_by_department(db, department=department)
    return db.query(Location).all()


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
    department: Annotated[str, Path(description="Department name", examples=["Cundinamarca"])],
):
    """Get all locations in a specific department."""
    return location.get_by_department(db, department=department)
