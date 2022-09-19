from typing import TypeVar, Generic

from fastapi_pagination.links import Page
from fastapi_pagination import Params as BaseParams

T = TypeVar("T")


class Params(BaseParams):
    size: int = 10


class JsonApiPage(Page[T], Generic[T]):
    """JSON:API 1.0 specification says that result key should be a `data`."""
    __params_type__ = Params

    class Config:
        allow_population_by_field_name = True
        fields = {"items": {"alias": "data"}}
