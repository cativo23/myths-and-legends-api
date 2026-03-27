from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import entity_type
from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.schemas.entity_type import EntityType as EntityTypeSchema

router = APIRouter(prefix="/entity-types", tags=["entity-types"])


@router.get(
    "/",
    response_model=List[EntityTypeSchema],
    summary="List Entity Types",
    description="Retrieve all entity types representing mythological origins (e.g., Egyptian, Greek, Norse).",
    responses={
        200: {"description": "Successful retrieval of entity types"},
    },
)
async def list_entity_types(
    db: Annotated[Session, Depends(get_db)],
    sort: Annotated[str | None, Query(description="Sort field", examples=["name", "id"])] = "name",
    order: Annotated[str, Query(description="Sort order (asc, desc)", examples=["asc", "desc"])] = "asc",
):
    """List all entity types."""
    entity_types = db.query(EntityType).all()

    # Sort results
    if order.lower() == "desc":
        return sorted(entity_types, key=lambda x: getattr(x, sort, x.id), reverse=True)
    return sorted(entity_types, key=lambda x: getattr(x, sort, x.id))


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
async def get_entity_type(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity Type ID", examples=[1])],
):
    """Get entity type by ID."""
    db_entity_type = entity_type.get(db, id=id)
    if not db_entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    return db_entity_type
