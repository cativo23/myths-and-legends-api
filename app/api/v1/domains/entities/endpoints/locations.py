from typing import Annotated, List

from fastapi import APIRouter, Depends, Path, Query, HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db, get_current_active_superuser
from app.api.v1.domains.entities.services import location
from app.api.v1.domains.entities.models.location import Location
from app.api.v1.domains.entities.schemas.location import (
    Location as LocationSchema,
    LocationCreate,
    LocationUpdate,
)
from app.api.v1.domains.users.models.user import User as UserModel

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
def list_locations(
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
def get_location(
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
def get_location_by_department(
    db: Annotated[Session, Depends(get_db)],
    department: Annotated[
        str,
        Path(max_length=200, description="Department name", examples=["Cundinamarca"]),
    ],
):
    """Get all locations in a specific department."""
    return location.get_by_department(db, department=department)


@router.post(
    "/",
    response_model=LocationSchema,
    status_code=201,
    summary="Create Location",
    description="Create a new location. Requires superuser privileges.",
    responses={
        201: {"description": "Location successfully created"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def create_location(
    db: Annotated[Session, Depends(get_db)],
    location_in: LocationCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Create a new location. Requires superuser privileges."""
    return location.create(db, obj_in=location_in)


@router.put(
    "/{id:int}",
    response_model=LocationSchema,
    summary="Update Location",
    description="Update an existing location by ID. Requires superuser privileges.",
    responses={
        200: {"description": "Location successfully updated"},
        404: {"description": "Location not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def update_location(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Location ID", examples=[1])],
    location_in: LocationUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Update a location. Requires superuser privileges."""
    db_location = location.get(db, item_id=id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location.update(db, db_obj=db_location, obj_in=location_in)


@router.delete(
    "/{id:int}",
    status_code=204,
    summary="Delete Location",
    description="Delete a location by ID. Requires superuser privileges.",
    responses={
        204: {"description": "Location successfully deleted"},
        404: {"description": "Location not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def delete_location(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Location ID", examples=[1])],
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Delete a location. Requires superuser privileges."""
    db_location = location.get(db, item_id=id)
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    location.remove(db, item_id=id)
