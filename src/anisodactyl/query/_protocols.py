from typing import List, Protocol, runtime_checkable

from fastapi import Request

from anisodactyl.crud._protocols import FilterDict


@runtime_checkable
class QueryParserProtocol(Protocol):
    filters: List[FilterDict]
    sort: List[str]
    fields: List[str]

    def __init__(self, request: Request): ...
