from anisodactyl.query.django import DjangoQueryParams
from tests.app.routes import create_mock_request


class TestDjangoQueryParser:
    def test_basic_filter(self):
        """Standard key=value should default to 'eq'."""
        req = create_mock_request("name=alice")
        params = DjangoQueryParams(req)
        assert params.filters == [{"field": "name", "op": "eq", "value": "alice"}]

    def test_django_operator_filter(self):
        """field__op=value syntax should be parsed correctly."""
        req = create_mock_request("age__gt=20")
        params = DjangoQueryParams(req)
        assert params.filters == [{"field": "age", "op": "gt", "value": "20"}]

    def test_operator_mapping(self):
        """Django specific lookups like 'icontains' should map to protocol ops."""
        req = create_mock_request("email__icontains=@gmail.com")
        params = DjangoQueryParams(req)
        assert params.filters == [
            {"field": "email", "op": "contains", "value": "@gmail.com"}
        ]

    def test_field_with_underscores(self):
        """Fields that contain underscores themselves should be handled correctly."""
        req = create_mock_request("first_name__startswith=Al")
        params = DjangoQueryParams(req)
        assert params.filters == [
            {"field": "first_name", "op": "startswith", "value": "Al"}
        ]

    def test_ordering_parsing(self):
        """Should use 'ordering' keyword instead of 'sort'."""
        req = create_mock_request("ordering=-created_at,id")
        params = DjangoQueryParams(req)
        assert params.sort == ["-created_at", "id"]
        assert params.filters == []  # Ensure 'ordering' isn't treated as a filter

    def test_fields_parsing(self):
        """Standard fields selection."""
        req = create_mock_request("fields=id,name,email")
        params = DjangoQueryParams(req)
        assert params.fields == ["id", "name", "email"]

    def test_complex_query(self):
        """Combination of filters, ordering, and fields."""
        req = create_mock_request(
            "status__exact=active&ordering=-id&fields=name&price__lte=100"
        )
        params = DjangoQueryParams(req)
        assert {"field": "status", "op": "eq", "value": "active"} in params.filters
        assert {"field": "price", "op": "lte", "value": "100"} in params.filters
        assert params.sort == ["-id"]
        assert params.fields == ["name"]

    def test_invalid_operator_fallback(self):
        """
        If __ is used with an unknown operator, it should treat the whole
        string as the field name (Django nested lookup style).
        """
        req = create_mock_request("profile__settings__theme=dark")
        params = DjangoQueryParams(req)
        # 'theme' is not in ALLOWED_OPS, so the whole key remains the field
        assert params.filters == [
            {"field": "profile__settings__theme", "op": "eq", "value": "dark"}
        ]

    def test_rsplit_logic(self):
        """Ensure it splits on the last double underscore only."""
        req = create_mock_request("user__profile__name__contains=bob")
        params = DjangoQueryParams(req)
        assert params.filters == [
            {"field": "user__profile__name", "op": "contains", "value": "bob"}
        ]
