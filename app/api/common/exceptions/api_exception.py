from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from fastapi import Request, FastAPI, status


class APIException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, data: Any = None):
        self.message = message
        self.status = status_code
        self.data = data


class ExistsException(APIException):
    def __init__(self, name: str):
        super().__init__(message=f"{name} already exists", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class NotFoundException(APIException):
    def __init__(self, name: str):
        super().__init__(message=f"{name} does not exist")
        self.status = status.HTTP_404_NOT_FOUND


class InactiveException(APIException):
    def __init__(self, name: str):
        super().__init__(message=f"{name} is inactive")
        self.status = status.HTTP_422_UNPROCESSABLE_ENTITY


def add_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(APIException)
    async def exists_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status,
            content={
                "status": exc.status,
                "message": exc.message,
                "data": exc.data
            },
        )
