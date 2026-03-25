from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import entity_type
from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.schemas.entity_type import EntityType as EntityTypeSchema

router = APIRouter(prefix="/entity-types", tags=["entity-types"])


@router.get("/", response_model=list[EntityTypeSchema])
async def list_entity_types(
    db: Annotated[Session, Depends(get_db)],
    sort: Annotated[str | None, Query(description="Sort field")] = "name",
    order: Annotated[str, Query(description="Sort order")] = "asc",
):
    """List all entity types"""
    entity_types = db.query(EntityType).all()

    # Sort results
    if order.lower() == "desc":
        return sorted(entity_types, key=lambda x: getattr(x, sort, x.id), reverse=True)
    return sorted(entity_types, key=lambda x: getattr(x, sort, x.id))


@router.get("/{id}", response_model=EntityTypeSchema)
async def get_entity_type(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get entity type by ID"""
    db_entity_type = entity_type.get(db, id=id)
    if not db_entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    return db_entity_type
