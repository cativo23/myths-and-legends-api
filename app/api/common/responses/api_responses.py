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
            message=f"{obj_name} with this ID does not exist",
            data=None,
            status=status.HTTP_404_NOT_FOUND,
        ).dict(),
    )


def found(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiResponse(
            message=f"Successfully retrieved {obj_name}",
            data=jsonable_encoder(obj),
            status=status.HTTP_200_OK,
        ).dict(),
    )


def created(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=ApiResponse(
            message=f"{obj_name} created successfully",
            data=jsonable_encoder(obj),
            status=status.HTTP_201_CREATED,
        ).dict(),
    )


def updated(obj_name: str = None, obj: ModelType = None):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiResponse(
            message=f"{obj_name} updated successfully",
            data=jsonable_encoder(obj),
            status=status.HTTP_200_OK,
        ).dict(),
    )


def deleted(obj_name: str = None):
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ApiResponse(
            message=f"{obj_name} deleted successfully",
            data=None,
            status=status.HTTP_200_OK,
        ).dict(),
    )
