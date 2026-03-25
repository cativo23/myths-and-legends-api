from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiResponse(BaseModel):
    status: int = 200
    message: str = ""
    data: Any = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
