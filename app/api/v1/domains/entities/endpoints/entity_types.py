from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db, get_current_active_superuser
from app.api.v1.domains.entities.services import entity_type
from app.api.v1.domains.entities.models.entity_type import EntityType
from app.api.v1.domains.entities.schemas.entity_type import (
    EntityType as EntityTypeSchema,
    EntityTypeCreate,
    EntityTypeUpdate,
)
from app.api.v1.domains.users.models.user import User as UserModel

router = APIRouter(prefix="/entity-types", tags=["entity-types"])


@router.get(
    "/",
    response_model=Page[EntityTypeSchema],
    summary="List Entity Types",
    description="Retrieve a paginated list of entity types representing mythological origins (e.g., Egyptian, Greek, Norse).",
    responses={
        200: {"description": "Successful retrieval of entity types"},
    },
)
def list_entity_types(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    sort: Annotated[
        Literal["name", "id"],
        Query(description="Sort field", examples=["name", "id"]),
    ] = "name",
    order: Annotated[
        str, Query(description="Sort order (asc, desc)", examples=["asc", "desc"])
    ] = "asc",
):
    """List all entity types, paginated and sorted at the database level."""
    sort_column = getattr(EntityType, sort)
    stmt = select(EntityType).order_by(
        sort_column.desc() if order.lower() == "desc" else sort_column.asc()
    )
    return paginate(db, stmt, Params(page=page, size=size))


@router.get(
    "/{id}",
    response_model=EntityTypeSchema,
    summary="Get Entity Type",
    description="Retrieve a specific entity type by ID.",
    responses={
        200: {"description": "Successful retrieval of entity type"},
        404: {"description": "Entity type not found"},
    },
)
def get_entity_type(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity Type ID", examples=[1])],
):
    """Get entity type by ID."""
    db_entity_type = entity_type.get(db, item_id=id)
    if not db_entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    return db_entity_type


@router.post(
    "/",
    response_model=EntityTypeSchema,
    status_code=201,
    summary="Create Entity Type",
    description="Create a new entity type. Requires superuser privileges.",
    responses={
        201: {"description": "Entity type successfully created"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def create_entity_type(
    db: Annotated[Session, Depends(get_db)],
    entity_type_in: EntityTypeCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Create a new entity type. Requires superuser privileges."""
    return entity_type.create(db, obj_in=entity_type_in)


@router.put(
    "/{id}",
    response_model=EntityTypeSchema,
    summary="Update Entity Type",
    description="Update an existing entity type by ID. Requires superuser privileges.",
    responses={
        200: {"description": "Entity type successfully updated"},
        404: {"description": "Entity type not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def update_entity_type(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity Type ID", examples=[1])],
    entity_type_in: EntityTypeUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Update an entity type. Requires superuser privileges."""
    db_entity_type = entity_type.get(db, item_id=id)
    if not db_entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    return entity_type.update(db, db_obj=db_entity_type, obj_in=entity_type_in)


@router.delete(
    "/{id}",
    status_code=204,
    summary="Delete Entity Type",
    description="Delete an entity type by ID. Requires superuser privileges.",
    responses={
        204: {"description": "Entity type successfully deleted"},
        404: {"description": "Entity type not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def delete_entity_type(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity Type ID", examples=[1])],
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Delete an entity type. Requires superuser privileges."""
    db_entity_type = entity_type.get(db, item_id=id)
    if not db_entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    entity_type.remove(db, item_id=id)
