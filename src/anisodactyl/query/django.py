from fastapi import Request

from anisodactyl.query._protocols import ALLOWED_OPS, QueryParserProtocol


class DjangoQueryParams(QueryParserProtocol):
    """
    Django REST Framework style URL spec:

    Filters:
    ?key__operator=value
    ?key=value

    Sorting:
    ?ordering=-key,key

    Fields:
    ?fields=a,b,c
    """

    def __init__(self, request: Request):
        self.filters = []
        self.sort = []
        self.fields = []

        # Django-specific operators to Protocol operators
        op_mapping = {
            "exact": "eq",
            "iexact": "eq",
            "icontains": "contains",
            "istartswith": "startswith",
            "iendswith": "endswith",
        }

        for key, value in request.query_params.items():
            # HANDLE RESERVED KEYWORDS
            if key == "ordering":
                self.sort = value.split(",")
                continue
            if key == "fields":
                self.fields = value.split(",")
                continue

            if "__" in key:
                # ?name__contains=bob
                field_path, op = key.rsplit("__", 1)
                op = op.lower()
                op = op_mapping.get(op, op)
                if op in ALLOWED_OPS:
                    self.filters.append({"field": field_path, "op": op, "value": value})
                else:
                    self.filters.append({"field": key, "op": "eq", "value": value})
            else:
                # ?name=bob
                self.filters.append({"field": key, "op": "eq", "value": value})
