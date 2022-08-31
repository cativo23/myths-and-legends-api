from pydantic import BaseModel


class ApiResponse(BaseModel):
    status: int
    message: str
    data: dict
