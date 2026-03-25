from typing import TypeVar, Generic

from fastapi_pagination.links import Page
from fastapi_pagination import Params as BaseParams
from pydantic import ConfigDict, Field

T = TypeVar("T")


class Params(BaseParams):
    size: int = 10


class JsonApiPage(Page[T], Generic[T]):
    """JSON:API 1.0 specification says that result key should be a `data`."""

    __params_type__ = Params

    model_config = ConfigDict(populate_by_name=True)

    # Override items field to use 'data' alias for JSON:API compliance
    items: T = Field(alias="data")
