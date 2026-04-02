from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db
from app.api.v1.entities.services import source
from app.api.v1.entities.models.source import Source
from app.api.v1.entities.schemas.source import Source as SourceSchema
from app.api.v1.entities.enums import SourceType

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get(
    "/",
    response_model=List[SourceSchema],
    summary="List Sources",
    description="Retrieve all sources, optionally filtered by type and sorted.",
    responses={
        200: {"description": "Successful retrieval of sources"},
    },
)
async def list_sources(
    db: Annotated[Session, Depends(get_db)],
    source_type: Annotated[
        SourceType | None,
        Query(
            description="Filter by source type",
            examples=["Book", "Website", "Manuscript", "Oral Tradition"],
        ),
    ] = None,
    sort: Annotated[
        str | None, Query(description="Sort field", examples=["title", "author", "id"])
    ] = "name",
    order: Annotated[
        str, Query(description="Sort order (asc, desc)", examples=["asc", "desc"])
    ] = "asc",
):
    """List all sources, optionally filtered by type and sorted."""
    query = db.query(Source)
    if source_type:
        query = query.filter(Source.source_type == source_type)
    sources = query.all()

    # Sort results
    if order.lower() == "desc":
        return sorted(sources, key=lambda x: getattr(x, sort, x.id), reverse=True)
    return sorted(sources, key=lambda x: getattr(x, sort, x.id))
