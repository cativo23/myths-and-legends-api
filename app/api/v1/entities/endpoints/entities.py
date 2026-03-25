from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params, paginate
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import entity, relation
from app.api.v1.entities.schemas.entity import Entity, EntityCreate, EntityUpdate
from app.api.v1.entities.schemas.entity_with_relations import (
    EntityWithRelations,
    EntityRelationSummary,
)
from app.api.v1.entities.enums import EntityTypeName, CategoryName

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=Page[Entity])
async def list_entities(
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
    sort: Annotated[str | None, Query(description="Sort field")] = "name",
    order: Annotated[str, Query(description="Sort order")] = "asc",
):
    """List all entities with optional filters"""
    entities = entity.get_multi(
        db,
        entity_type=entity_type,
        category=category,
        is_active=is_active,
        skip=(page - 1) * size,
        limit=size,
    )
    return paginate(entities, Params(page=page, size=size))


@router.get("/search", response_model=list[Entity])
async def search_entities(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(min_length=1, description="Search term")],
):
    """Search entities by name, description, or origin"""
    return entity.search(db, term=q)


@router.get("/{id}", response_model=EntityWithRelations)
async def get_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get entity by ID with all nested relations"""
    db_entity = entity.get(db, id=id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get relations graph
    relations = entity.get_relations_graph(db, entity_id=id)

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
                    r.relation_type.value
                    if hasattr(r.relation_type, "value")
                    else r.relation_type
                ),
                description=r.description,
                related_entity_id=related_entity.id,
                related_entity_name=related_entity.name,
                direction=direction,
            )
        )

    return EntityWithRelations(
        id=db_entity.id,
        name=db_entity.name,
        alternative_names=db_entity.alternative_names,
        category_id=db_entity.category_id,
        entity_type_id=db_entity.entity_type_id,
        description=db_entity.description,
        origin=db_entity.origin,
        behavior=db_entity.behavior,
        image_url=db_entity.image_url,
        is_active=db_entity.is_active,
        created_at=db_entity.created_at,
        category=db_entity.category,
        entity_type=db_entity.entity_type,
        characteristics=db_entity.characteristics,
        locations=db_entity.locations,
        sources=db_entity.sources,
        relations=relations_summary,
    )


@router.post("/", response_model=Entity, status_code=201)
async def create_entity(
    db: Annotated[Session, Depends(get_db)],
    entity_in: EntityCreate,
):
    """Create a new entity"""
    return entity.create(db, obj_in=entity_in)


@router.put("/{id}", response_model=Entity)
async def update_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
    entity_in: EntityUpdate,
):
    """Update an entity"""
    db_entity = entity.get(db, id=id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity.update(db, db_obj=db_entity, obj_in=entity_in)


@router.delete("/{id}", status_code=204)
async def delete_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Delete an entity"""
    db_entity = entity.get(db, id=id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    entity.remove(db, id=id)


@router.get("/{id}/relations", response_model=list[EntityRelationSummary])
async def get_entity_relations(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0)],
):
    """Get all relations for an entity"""
    db_entity = entity.get(db, id=id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    relations = relation.get_by_entity(db, entity_id=id)

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
                    r.relation_type.value
                    if hasattr(r.relation_type, "value")
                    else r.relation_type
                ),
                description=r.description,
                related_entity_id=related_entity.id,
                related_entity_name=related_entity.name,
                direction=direction,
            )
        )

    return relations_summary
