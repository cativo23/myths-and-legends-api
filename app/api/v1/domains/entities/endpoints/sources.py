from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db, get_current_active_superuser
from app.api.v1.domains.entities.services import source
from app.api.v1.domains.entities.models.source import Source
from app.api.v1.domains.entities.schemas.source import (
    Source as SourceSchema,
    SourceCreate,
    SourceUpdate,
)
from app.api.v1.domains.entities.enums import SourceType
from app.api.v1.domains.users.models.user import User as UserModel

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get(
    "/",
    response_model=Page[SourceSchema],
    summary="List Sources",
    description="Retrieve a paginated list of sources, optionally filtered by type and sorted.",
    responses={
        200: {"description": "Successful retrieval of sources"},
    },
)
def list_sources(
    db: Annotated[Session, Depends(get_db)],
    source_type: Annotated[
        SourceType | None,
        Query(
            description="Filter by source type",
            examples=["Book", "Website", "Manuscript", "Oral Tradition"],
        ),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    sort: Annotated[
        Literal["id", "title", "author", "source_type"],
        Query(description="Sort field", examples=["title", "author", "id"]),
    ] = "id",
    order: Annotated[
        str, Query(description="Sort order (asc, desc)", examples=["asc", "desc"])
    ] = "asc",
):
    """List all sources, optionally filtered by type, paginated and sorted at the database level."""
    stmt = select(Source)
    if source_type:
        stmt = stmt.where(Source.source_type == source_type)

    sort_column = getattr(Source, sort)
    stmt = stmt.order_by(
        sort_column.desc() if order.lower() == "desc" else sort_column.asc()
    )
    return paginate(db, stmt, Params(page=page, size=size))


@router.get(
    "/{id}",
    response_model=SourceSchema,
    summary="Get Source by ID",
    description="Retrieve a single source by its ID.",
    responses={
        200: {"description": "Successful retrieval of source"},
        404: {"description": "Source not found"},
    },
)
def get_source(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Source ID", examples=[1])],
):
    """Get a single source by its ID."""
    db_source = source.get(db, item_id=id)
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    return db_source


@router.post(
    "/",
    response_model=SourceSchema,
    status_code=201,
    summary="Create Source",
    description="Create a new source. Requires superuser privileges.",
    responses={
        201: {"description": "Source successfully created"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def create_source(
    db: Annotated[Session, Depends(get_db)],
    source_in: SourceCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Create a new source. Requires superuser privileges."""
    return source.create(db, obj_in=source_in)


@router.put(
    "/{id}",
    response_model=SourceSchema,
    summary="Update Source",
    description="Update an existing source by ID. Requires superuser privileges.",
    responses={
        200: {"description": "Source successfully updated"},
        404: {"description": "Source not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def update_source(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Source ID", examples=[1])],
    source_in: SourceUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Update a source. Requires superuser privileges."""
    db_source = source.get(db, item_id=id)
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source.update(db, db_obj=db_source, obj_in=source_in)


@router.delete(
    "/{id}",
    status_code=204,
    summary="Delete Source",
    description="Delete a source by ID. Requires superuser privileges.",
    responses={
        204: {"description": "Source successfully deleted"},
        404: {"description": "Source not found"},
        401: {"description": "Unauthorized - No valid token provided"},
        403: {"description": "Forbidden - User is not a superuser"},
    },
)
def delete_source(
    db: Annotated[Session, Depends(get_db)],
    id: Annotated[int, Path(gt=0, description="Source ID", examples=[1])],
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """Delete a source. Requires superuser privileges."""
    db_source = source.get(db, item_id=id)
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.remove(db, item_id=id)
