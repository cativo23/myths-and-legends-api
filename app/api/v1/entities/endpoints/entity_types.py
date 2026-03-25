from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.entities.services.entity_type import EntityTypeService
from app.api.v1.entities.models.entity_type import EntityType
from app.api.v1.entities.schemas.entity_type import EntityType as EntityTypeSchema

router = APIRouter(prefix="/entity-types", tags=["entity-types"])

entity_type_service = EntityTypeService()


@router.get("/", response_model=list[EntityTypeSchema])
def list_entity_types(db: Annotated[Session, Depends(get_db)]):
    """List all entity types"""
    return db.query(EntityType).all()


@router.get("/{id}", response_model=EntityTypeSchema)
def get_entity_type(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get entity type by ID"""
    entity_type = entity_type_service.get(db, id=id)
    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")
    return entity_type
