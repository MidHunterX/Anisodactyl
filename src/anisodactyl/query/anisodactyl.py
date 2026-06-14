from fastapi import Request

from anisodactyl.query._protocols import ALLOWED_OPS, QueryParserProtocol


class QueryParams(QueryParserProtocol):
    """
    Anisodactyl URL spec:
    ?key=operator:value -> filters[{"field": key, "op": operator, "value": value}]
    ?sort=-key,key      -> sort[key, -key]
    ?fields=a,b,c       -> fields[a, b, c]
    """

    def __init__(self, request: Request):
        self.filters = []
        self.sort = []
        self.fields = []

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
                op, potential_value = value.split(":", 1)
                if op.lower() in ALLOWED_OPS:
                    op = op.lower()
                    val = potential_value
                else:
                    # ?key=value_with_colon
                    # likely a timestamp or a value containing a colon ("10:00 AM")
                    op = "eq"
                    val = value
                self.filters.append({"field": key, "op": op, "value": val})
            else:
                # ?key=value
                self.filters.append({"field": key, "op": "eq", "value": value})
