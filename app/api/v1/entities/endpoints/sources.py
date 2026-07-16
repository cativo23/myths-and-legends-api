from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.models.source import Source
from app.api.v1.entities.schemas.source import Source as SourceSchema
from app.api.v1.entities.enums import SourceType

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
