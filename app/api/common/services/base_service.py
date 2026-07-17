from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi_pagination.bases import AbstractPage, AbstractParams
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import ArgumentError, IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.common.exceptions.api_exception import RelationshipNotFoundException
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    SQLAlchemy 2.0 CRUD Service with default methods for Create, Read, Update, Delete.

    **Parameters:**
    - `model`: A SQLAlchemy model class
    - `schema`: A Pydantic model (schema) class
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def _build_query(self, relations: List[str] | None = None):
        """Build a select query with optional eager loading, ordered by id for
        stable pagination (without an explicit ORDER BY, offset/limit results
        are not guaranteed to be stable across concurrent writes)."""
        stmt = select(self.model).order_by(self.model.id)
        if relations:
            stmt = stmt.options(
                *[selectinload(getattr(self.model, r)) for r in relations]
            )
        return stmt

    def get(
        self, db: Session, item_id: int, relations: List[str] | None = None
    ) -> Optional[ModelType]:
        """Get a single item by ID with optional relations."""
        try:
            stmt = self._build_query(relations).where(self.model.id == item_id)
            return db.execute(stmt).scalar_one_or_none()
        except ArgumentError as error:
            raise RelationshipNotFoundException(
                name=error.args[0].split('"')[1],
            )

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        relations: List[str] | None = None,
    ) -> list[ModelType]:
        """Get multiple items with pagination and optional relations."""
        try:
            stmt = self._build_query(relations).offset(skip).limit(limit)
            return db.execute(stmt).scalars().all()
        except ArgumentError as error:
            raise RelationshipNotFoundException(
                name=error.args[0].split('"')[1],
            )

    def get_all(
        self,
        db: Session,
        relations: List[str] | None = None,
        *,
        params: AbstractParams | None = None,
    ) -> AbstractPage:
        """Get all items with pagination (fastapi-pagination).

        `params` is optional: when omitted, fastapi-pagination resolves it
        from the request's own page/size query params via its ContextVar
        (wired up by `add_pagination(app)`). Pass it explicitly when the
        caller already parsed its own page/size (e.g. because it also has
        other query params to validate) so the two don't drift out of sync.
        """
        try:
            stmt = self._build_query(relations)
            return paginate(db, stmt, params)
        except ArgumentError as error:
            raise RelationshipNotFoundException(
                name=error.args[0].split('"')[1],
            )

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new item."""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        try:
            db.commit()
        except IntegrityError:
            # Assumes the violation is a unique-constraint conflict (true for
            # every current caller, which only have unique-name columns and
            # no FK columns on create/update). If a future model added here
            # has FK columns, an FK-violation IntegrityError would also hit
            # this branch and get a misleading "already exists" message.
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"A {self.model.__name__} with these values already exists.",
            )
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """Update an existing item."""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        try:
            db.commit()
        except IntegrityError:
            # Assumes the violation is a unique-constraint conflict (true for
            # every current caller, which only have unique-name columns and
            # no FK columns on create/update). If a future model added here
            # has FK columns, an FK-violation IntegrityError would also hit
            # this branch and get a misleading "already exists" message.
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"A {self.model.__name__} with these values already exists.",
            )
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, item_id: int) -> ModelType:
        """Delete an item by ID."""
        obj = self.get(db, item_id=item_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def validate_existence(self, db: Session, *, item_id: int) -> Optional[ModelType]:
        """Validate that an item exists by ID."""
        return self.get(db, item_id=item_id)

    def exists(self, db: Session, *, item_id: int) -> bool:
        """Check whether a row with this ID exists, without fetching or eager-loading it."""
        stmt = select(self.model.id).where(self.model.id == item_id)
        return db.execute(stmt).scalar_one_or_none() is not None
