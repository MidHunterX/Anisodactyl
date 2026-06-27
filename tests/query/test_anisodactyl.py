from anisodactyl.query.anisodactyl import QueryParams
from tests.app.routes import create_mock_request


class TestQueryParser:
    def test_basic_filter(self):
        req = create_mock_request("name=alice")
        params = QueryParams(req)
        assert params.filters == [{"field": "name", "op": "eq", "value": "alice"}]

    def test_operator_filter(self):
        req = create_mock_request("age=gt:20")
        params = QueryParams(req)
        assert params.filters == [{"field": "age", "op": "gt", "value": "20"}]

    def test_sort_parsing(self):
        req = create_mock_request("sort=-created_at,id")
        params = QueryParams(req)
        assert params.sort == ["-created_at", "id"]

    def test_fields_parsing(self):
        req = create_mock_request("fields=id,name,email")
        params = QueryParams(req)
        assert params.fields == ["id", "name", "email"]

    def test_complex_query(self):
        req = create_mock_request("status=eq:active&sort=-id&fields=name")
        params = QueryParams(req)
        assert params.filters == [{"field": "status", "op": "eq", "value": "active"}]
        assert params.sort == ["-id"]
        assert params.fields == ["name"]

    def test_value_with_colon(self):
        req = create_mock_request("time=10:00")
        params = QueryParams(req)
        assert params.filters == [{"field": "time", "op": "eq", "value": "10:00"}]

    def test_invalid_operator_fallback(self):
        req = create_mock_request("key=notanop:value")
        params = QueryParams(req)
        assert params.filters == [
            {"field": "key", "op": "eq", "value": "notanop:value"}
        ]
