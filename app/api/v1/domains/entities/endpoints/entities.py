from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db, get_current_active_superuser
from app.api.v1.domains.entities.services import entity, relation
from app.api.v1.domains.entities.schemas.entity import (
    Entity,
    EntityCreate,
    EntityUpdate,
)
from app.api.v1.domains.entities.schemas.entity_with_relations import (
    EntityWithRelations,
    EntityRelationSummary,
)
from app.api.v1.domains.entities.schemas.entity_relation import (
    EntityRelation,
    CreateRelationRequest,
)
from app.api.v1.domains.entities.enums import EntityTypeName, CategoryName
from app.api.v1.domains.users.models.user import User as UserModel

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get(
    "/",
    response_model=Page[Entity],
    summary="List Entities",
    description="Retrieve a paginated list of mythological entities with optional filters.",
    responses={
        200: {"description": "Successful retrieval of entities"},
    },
)
def list_entities(
    db: Annotated[Session, Depends(get_db)],
    entity_type: Annotated[
        EntityTypeName | None,
        Query(
            description="Filter by entity type (e.g., Egyptian, Greek, Norse)",
            examples=["Egyptian", "Greek"],
        ),
    ] = None,
    category: Annotated[
        CategoryName | None,
        Query(
            description="Filter by category (e.g., Deity, Creature, Place)",
            examples=["Deity", "Creature"],
        ),
    ] = None,
    is_active: Annotated[
        bool | None, Query(description="Filter by active status")
    ] = True,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    sort: Annotated[str | None, Query(description="Sort field")] = "name",
    order: Annotated[str, Query(description="Sort order (asc, desc)")] = "asc",
):
    """List all entities with optional filters and pagination."""
    return entity.get_paginated(
        db,
        entity_type=entity_type,
        category=category,
        is_active=is_active,
        params=Params(page=page, size=size),
    )


@router.get(
    "/search",
    response_model=List[Entity],
    summary="Search Entities",
    description="Search entities by name, description, or origin using a free-text query.",
    responses={
        200: {"description": "Successful search results"},
    },
)
def search_entities(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=200,
            description="Search term (searches name, description, and origin)",
            examples=["Zeus", "underworld", "god of thunder"],
        ),
    ],
):
    """Search entities by name, description, or origin."""
    return entity.search(db, term=q)


@router.get(
    "/{id}",
    response_model=EntityWithRelations,
    summary="Get Entity",
    description="Retrieve a specific entity by ID with all its nested relations (category, type, characteristics, locations, sources, and entity relations).",
    responses={
        200: {"description": "Successful retrieval of entity with relations"},
        404: {"description": "Entity not found"},
    },
)
def get_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity ID", examples=[1])],
):
    """Get entity by ID with all nested relations."""
    db_entity = entity.get(db, item_id=id)
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


@router.post(
    "/",
    response_model=Entity,
    status_code=201,
    summary="Create Entity",
    description="Create a new mythological entity. Requires superuser privileges.",
    responses={
        201: {"description": "Entity successfully created"},
        400: {"description": "Invalid input data"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def create_entity(
    db: Annotated[Session, Depends(get_db)],
    entity_in: EntityCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Create a new entity. Requires superuser privileges."""
    return entity.create(db, obj_in=entity_in)


@router.put(
    "/{id}",
    response_model=Entity,
    summary="Update Entity",
    description="Update an existing entity by ID. Requires superuser privileges.",
    responses={
        200: {"description": "Entity successfully updated"},
        404: {"description": "Entity not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def update_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity ID", examples=[1])],
    entity_in: EntityUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Update an entity. Requires superuser privileges."""
    db_entity = entity.get(db, item_id=id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity.update(db, db_obj=db_entity, obj_in=entity_in)


@router.delete(
    "/{id}",
    status_code=204,
    summary="Delete Entity",
    description="Delete an entity by ID. Requires superuser privileges.",
    responses={
        204: {"description": "Entity successfully deleted"},
        404: {"description": "Entity not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def delete_entity(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity ID", examples=[1])],
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Delete an entity. Requires superuser privileges."""
    db_entity = entity.get(db, item_id=id)
    if not db_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    entity.remove(db, item_id=id)


@router.get(
    "/{id}/relations",
    response_model=List[EntityRelationSummary],
    summary="Get Entity Relations",
    description="Retrieve all relations for a specific entity (e.g., parent-child, siblings, enemies).",
    responses={
        200: {"description": "Successful retrieval of relations"},
        404: {"description": "Entity not found"},
    },
)
def get_entity_relations(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Entity ID", examples=[1])],
):
    """Get all relations for an entity."""
    if not entity.exists(db, item_id=id):
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


@router.post(
    "/{id}/relations",
    response_model=EntityRelation,
    status_code=201,
    summary="Create Entity Relation",
    description="Create a relation between two entities. Symmetric relation "
    "types (SIBLINGS, ALLIES, ENEMIES) automatically create the reverse "
    "relation too. Requires superuser privileges.",
    responses={
        201: {"description": "Relation successfully created"},
        400: {"description": "An entity cannot have a relation to itself"},
        404: {"description": "Entity not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
        409: {
            "description": "This exact relation (origin, destination, type) already exists"
        },
    },
)
def create_entity_relation(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Origin entity ID", examples=[1])],
    relation_in: CreateRelationRequest,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Create a relation from this entity to another. Requires superuser privileges."""
    origin_entity = entity.get(db, item_id=id)
    if not origin_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    if relation_in.entity_destination_id == id:
        # Checked only after confirming the origin exists, so a self-relation
        # against a nonexistent entity correctly reports 404 rather than 400.
        # Rejected unconditionally, regardless of relation_type: for symmetric
        # types (SIBLINGS/ALLIES/ENEMIES) the forward and reverse rows created
        # by create_bidirectional() would otherwise be identical, tripping
        # the uq_entity_relation_unique constraint and surfacing as an
        # unhandled 500; for non-symmetric types (e.g. MOTHER_CHILD) it would
        # succeed but be semantically nonsensical (an entity as its own
        # parent), so it's rejected the same way for both.
        raise HTTPException(
            status_code=400, detail="An entity cannot have a relation to itself"
        )
    destination_entity = entity.get(db, item_id=relation_in.entity_destination_id)
    if not destination_entity:
        raise HTTPException(status_code=404, detail="Destination entity not found")

    forward, _reverse = relation.create_bidirectional(
        db,
        origin_id=id,
        destination_id=relation_in.entity_destination_id,
        relation_type=relation_in.relation_type,
        description=relation_in.description,
    )
    return EntityRelation(
        id=forward.id,
        entity_origin_id=forward.entity_origin_id,
        entity_destination_id=forward.entity_destination_id,
        relation_type=forward.relation_type,
        description=forward.description,
        entity_origin_name=origin_entity.name,
        entity_destination_name=destination_entity.name,
    )
