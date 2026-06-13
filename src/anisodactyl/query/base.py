from typing import Any, List, Protocol, runtime_checkable

from fastapi import Request
from typing_extensions import TypedDict


class FilterDict(TypedDict):
    field: str
    op: str
    value: Any


@runtime_checkable
class QueryParserProtocol(Protocol):
    """
    Any class passed to RouterBase as a query parser must implement this
    structure.
    """

    filters: List[FilterDict]
    sort: List[str]
    fields: List[str]

    def __init__(self, request: Request): ...
