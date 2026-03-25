from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params, paginate
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.entities.services.entity import EntityService
from app.api.v1.entities.services.entity_relation import EntityRelationService
from app.api.v1.entities.schemas.entity import Entity, EntityCreate, EntityUpdate
from app.api.v1.entities.schemas.entity_with_relations import (
    EntityWithRelations,
    EntityRelationSummary,
)
from app.api.v1.entities.enums import EntityTypeName, CategoryName

router = APIRouter(prefix="/entities", tags=["entities"])

entity_service = EntityService()
relation_service = EntityRelationService()


@router.get("/", response_model=Page[Entity])
def list_entities(
    db: Annotated[Session, Depends(get_db)],
    entity_type: Annotated[
        EntityTypeName | None, Query(description="Filter by entity type")
    ] = None,
    category: Annotated[
        CategoryName | None, Query(description="Filter by category")
    ] = None,
    is_active: Annotated[
        bool | None, Query(description="Filter by active status")
    ] = True,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List all entities with optional filters"""
    entities = entity_service.get_multi(
        db,
        entity_type=entity_type,
        category=category,
        is_active=is_active,
        skip=(page - 1) * size,
        limit=size,
    )
    # Disable pagination check since we're using simple paginate
    from fastapi_pagination.utils import disable_installed_extensions_check

    disable_installed_extensions_check()
    return paginate(entities, Params(page=page, size=size))


@router.get("/search", response_model=list[Entity])
def search_entities(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(min_length=1, description="Search term")],
):
    """Search entities by name, description, or origin"""
    return entity_service.search(db, term=q)


@router.get("/{id}", response_model=EntityWithRelations)
def get_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get entity by ID with all nested relations"""
    entity = entity_service.get(db, id=id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get relations graph
    relations = entity_service.get_relations_graph(db, entity_id=id)

    # Build response with relations
    relations_summary = []
    for r in relations:
        if r.entity_origin_id == id:
            related_entity = r.entity_destination
            direction = "origin"
        else:
            related_entity = r.entity_origin
            direction = "destination"

        relations_summary.append(
            EntityRelationSummary(
                id=r.id,
                relation_type=(
                    r.relation_type
                    if isinstance(r.relation_type, str)
                    else r.relation_type.value
                ),
                description=r.description,
                related_entity_id=related_entity.id,
                related_entity_name=related_entity.name,
                direction=direction,
            )
        )

    return EntityWithRelations(
        id=entity.id,
        name=entity.name,
        alternative_names=entity.alternative_names,
        category_id=entity.category_id,
        entity_type_id=entity.entity_type_id,
        description=entity.description,
        origin=entity.origin,
        behavior=entity.behavior,
        image_url=entity.image_url,
        is_active=entity.is_active,
        created_at=entity.created_at,
        category=entity.category,
        entity_type=entity.entity_type,
        characteristics=entity.characteristics,
        locations=entity.locations,
        sources=entity.sources,
        relations=relations_summary,
    )


@router.post("/", response_model=Entity, status_code=201)
def create_entity(
    db: Annotated[Session, Depends(get_db)],
    entity_in: Annotated[EntityCreate, Depends()],
):
    """Create a new entity"""
    return entity_service.create(db, obj_in=entity_in)


@router.put("/{id}", response_model=Entity)
def update_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
    entity_in: Annotated[EntityUpdate, Depends()],
):
    """Update an entity"""
    entity = entity_service.get(db, id=id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity_service.update(db, db_obj=entity, obj_in=entity_in)


@router.delete("/{id}", status_code=204)
def delete_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Delete an entity"""
    entity = entity_service.get(db, id=id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    entity_service.remove(db, id=id)
    return None


@router.get("/{id}/relations", response_model=list[EntityRelationSummary])
def get_entity_relations(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get all relations for an entity"""
    entity = entity_service.get(db, id=id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    relations = relation_service.get_by_entity(db, entity_id=id)

    # Build response
    relations_summary = []
    for r in relations:
        if r.entity_origin_id == id:
            related_entity = r.entity_destination
            direction = "origin"
        else:
            related_entity = r.entity_origin
            direction = "destination"

        relations_summary.append(
            EntityRelationSummary(
                id=r.id,
                relation_type=(
                    r.relation_type
                    if isinstance(r.relation_type, str)
                    else r.relation_type.value
                ),
                description=r.description,
                related_entity_id=related_entity.id,
                related_entity_name=related_entity.name,
                direction=direction,
            )
        )

    return relations_summary
