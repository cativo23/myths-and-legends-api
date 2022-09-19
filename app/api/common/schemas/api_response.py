from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    def __init__(self, message: str, data: Any = None, status: int = 200, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.status = status
        self.data = data

    status: int = 200
    message: str = ""
    data: Any = None
