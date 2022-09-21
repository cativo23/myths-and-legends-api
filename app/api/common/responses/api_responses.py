from typing import TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette import status

from app.db.base_class import Base

from ..schemas import ApiResponse

ModelType = TypeVar("ModelType", bound=Base)


def not_found(obj_name: str = None):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ApiResponse(
            message="The %s with this id does not exist in the system." % obj_name,
            data=None,
            status=status.HTTP_404_NOT_FOUND
        ).dict()
    )


def found(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiResponse(
            message="The %s is returned correctly" % obj_name,
            data=jsonable_encoder(obj),
            status=status.HTTP_200_OK
        ).dict()
    )


def created(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=ApiResponse(
            message="The %s is created correctly" % obj_name,
            data=jsonable_encoder(obj),
            status=status.HTTP_201_CREATED
        ).dict()
    )


def updated(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiResponse(
            message="The %s is updated correctly" % obj_name,
            data=jsonable_encoder(obj),
            status=status.HTTP_200_OK
        ).dict()
    )


def deleted(obj_name: str = None):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiResponse(
            message="The %s is deleted correctly" % obj_name,
            data=None,
            status=status.HTTP_200_OK
        ).dict()
    )