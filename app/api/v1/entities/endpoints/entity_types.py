from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import entity_type
from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.schemas.entity_type import EntityType as EntityTypeSchema

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
