from typing import List

from fastapi import Request

from ._protocols import FilterDict


class QueryParams:
    """
    Anisodactyl URL spec:
    ?key=operator:value -> filters[{"field": key, "op": operator, "value": value}]
    ?sort=-key,key      -> sort[key, -key]
    ?fields=a,b,c       -> fields[a, b, c]
    """

    def __init__(self, request: Request):
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
