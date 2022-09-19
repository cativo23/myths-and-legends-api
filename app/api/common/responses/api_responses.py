from typing import TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.db.base_class import Base

from ..schemas import ApiResponse

ModelType = TypeVar("ModelType", bound=Base)


def not_found(obj_name: str = None):
    return JSONResponse(
        status_code=404,
        content=ApiResponse(
            message="The %s with this id does not exist in the system." % obj_name,
            data=None,
            status=404
        ).dict()
    )


def found(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=200,
        content=ApiResponse(
            message="The %s is returned correctly" % obj_name,
            data=jsonable_encoder(obj),
            status=200
        ).dict()
    )


def created(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=201,
        content=ApiResponse(
            message="The %s is created correctly" % obj_name,
            data=jsonable_encoder(obj),
            status=201
        ).dict()
    )


def updated(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=200,
        content=ApiResponse(
            message="The %s is updated correctly" % obj_name,
            data=jsonable_encoder(obj),
            status=200
        ).dict()
    )


def deleted(obj_name: str = None):
    return JSONResponse(
        status_code=200,
        content=ApiResponse(
            message="The %s is deleted correctly" % obj_name,
            data=None,
            status=200
        ).dict()
    )