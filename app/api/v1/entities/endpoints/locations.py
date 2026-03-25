from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.entities.services.location import LocationService
from app.api.v1.entities.models.location import Location
from app.api.v1.entities.schemas.location import Location as LocationSchema

router = APIRouter(prefix="/locations", tags=["locations"])

location_service = LocationService()


@router.get("/", response_model=list[LocationSchema])
def list_locations(
    db: Annotated[Session, Depends(get_db)],
    department: Annotated[str | None, Query(description="Filter by department")] = None,
):
    """List all locations, optionally filtered by department"""
    if department:
        return location_service.get_by_department(db, department=department)
    return db.query(Location).all()


@router.get("/{department}", response_model=list[LocationSchema])
def get_location_by_department(
    db: Annotated[Session, Depends(get_db)],
    department: Annotated[str, Path(description="Department name")],
):
    """Get all locations in a specific department"""
    return location_service.get_by_department(db, department=department)
