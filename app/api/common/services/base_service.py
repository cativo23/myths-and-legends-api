from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, subqueryload

from app.api.common.exceptions.api_exception import RelationshipNotFoundException
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD Service object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters:**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, item_id: Any, relations: dict) -> Optional[ModelType]:
        try:
            return db.query(self.model).filter(self.model.id == item_id) \
                .options(*[subqueryload(r) for r in relations]).first()
        except ArgumentError as error:
            raise RelationshipNotFoundException(
                name=error.args[0].split('"')[1],
            )

    def get_all(
            self, db: Session,
            relations: dict,
    ) -> AbstractPage:
        try:
            results = db.query(self.model).options(*[subqueryload(r) for r in relations])
            return paginate(results)
        except ArgumentError as error:
            raise RelationshipNotFoundException(
                name=error.args[0].split('"')[1],
            )

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
            self,
            db: Session,
            *,
            db_obj: ModelType,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, item_id: int) -> ModelType:
        obj = db.query(self.model).get(item_id)
        db.delete(obj)
        db.commit()
        return obj

    def validate_existence(self, db: Session, *, item_id: int) -> Optional[ModelType]:
        db_obj = self.get(db, item_id=item_id)
        if not db_obj:
            return None
        return db_obj
