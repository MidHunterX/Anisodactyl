from typing import List

from fastapi import Request

from .base import FilterDict, QueryParserProtocol


class QueryParams:
    """
    Anisodactyl URL spec:
    ?key=operator:value -> filtering
    ?sort=-key,key      -> sorting
    ?fields=a,b,c       -> field selection
    """

    def __init__(self: QueryParserProtocol, request: Request):
        self.filters: List[FilterDict] = []
        self.sort: List[str] = []
        self.fields: List[str] = []

        for key, value in request.query_params.items():
            # HANDLE RESERVED KEYWORDS
            if key == "sort":
                self.sort = value.split(",")
                continue
            if key == "fields":
                self.fields = value.split(",")
                continue

            # FILTERS
            if ":" in value:
                # ?key=operator:value
                op, val = value.split(":", 1)
                self.filters.append({"field": key, "op": op, "value": val})
            else:
                # ?key=value
                self.filters.append({"field": key, "op": "eq", "value": value})
