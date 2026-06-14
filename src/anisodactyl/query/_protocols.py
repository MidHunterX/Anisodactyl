from typing import List, Protocol, TypeVar, runtime_checkable

from fastapi import Request

from anisodactyl.crud._protocols import FilterDict

ALLOWED_OPS = {
    "eq",
    "ne",
    "gt",
    "lt",
    "gte",
    "lte",
    "contains",
    "startswith",
    "endswith",
}

QuerySourceT = TypeVar("QuerySourceT", contravariant=True)  # Request, dict ...


@runtime_checkable
class QueryParserProtocol(Protocol):
    filters: List[FilterDict]
    sort: List[str]
    fields: List[str]

    def __init__(self, request: Request): ...
