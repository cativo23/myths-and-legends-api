from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.entities.services.source import SourceService
from app.api.v1.entities.models.source import Source
from app.api.v1.entities.schemas.source import Source as SourceSchema
from app.api.v1.entities.enums import SourceType

router = APIRouter(prefix="/sources", tags=["sources"])

source_service = SourceService()


@router.get("/", response_model=list[SourceSchema])
def list_sources(
    db: Annotated[Session, Depends(get_db)],
    source_type: Annotated[
        SourceType | None, Query(description="Filter by source type")
    ] = None,
):
    """List all sources, optionally filtered by type"""
    if source_type:
        return db.query(Source).filter(Source.source_type == source_type).all()
    return db.query(Source).all()
