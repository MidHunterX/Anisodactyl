from anisodactyl.crud._protocols import CRUDProtocol
from anisodactyl.crud.sqlalchemy import CRUDBase
from anisodactyl.query._protocols import QueryParserProtocol
from anisodactyl.query.anisodactyl import QueryParams
from anisodactyl.query.django import DjangoQueryParams
from tests.app.models import Model
from tests.app.routes import create_mock_request


class TestProtocolConformance:
    """Test that implementations conform to protocols."""

    def test_crud_implements_protocol(self):
        """CRUD implementation should be recognized as a CRUDProtocol."""
        # Create instance with minimal requirements
        crud_instance = CRUDBase(model=Model)
        assert isinstance(crud_instance, CRUDProtocol)

    def test_anisodactyl_query_implements_protocol(self):
        """Anisodactyl QueryParser implements QueryParserProtocol."""
        request_mock = create_mock_request("name=alice&status=eq:active")
        parser = QueryParams(request_mock)
        assert isinstance(parser, QueryParserProtocol)

    def test_django_query_implements_protocol(self):
        """Django QueryParser implements QueryParserProtocol."""
        request_mock = create_mock_request("name=alice&status__exact=active")
        parser = DjangoQueryParams(request_mock)
        assert isinstance(parser, QueryParserProtocol)
