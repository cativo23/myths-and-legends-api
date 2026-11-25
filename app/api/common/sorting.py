"""Shared sorting for list endpoints.

Each endpoint declares its own `Literal` of allowed sort fields (so OpenAPI
documents them and anything else is a 422); the ordering itself lives here
so it is written once.
"""

from typing import Any, Literal, Type

from sqlalchemy import Select

SortOrder = Literal["asc", "desc"]


def apply_sort(stmt: Select, model: Type[Any], sort: str, order: SortOrder) -> Select:
    """Order `stmt` by `model.<sort>`, replacing any previous ORDER BY.

    `sort` MUST already be validated against a fixed set of column names by the
    caller. NULLs go last in both directions: Postgres and SQLite disagree by
    default, and the tests run on SQLite. `id` is the tie-breaker so offset
    pagination stays stable when many rows share the sort value.
    """
    column = getattr(model, sort)
    primary = column.desc() if order == "desc" else column.asc()
    clauses = [primary.nulls_last()]
    if sort != "id":
        clauses.append(model.id.asc())
    return stmt.order_by(None).order_by(*clauses)
