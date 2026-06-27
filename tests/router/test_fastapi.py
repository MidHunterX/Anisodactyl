import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from anisodactyl.crud.sqlalchemy import CRUDBase
from anisodactyl.router.fastapi import RouterBase
from tests.app.models import Model
from tests.app.schemas import CreateSchema, ResponseSchema, UpdateSchema


@pytest.mark.asyncio
class TestRouterBase:

    @pytest.fixture
    def app(self, override_get_db):
        """Temp FastAPI app for router testing"""
        application = FastAPI()
        crud = CRUDBase[Model, CreateSchema, UpdateSchema](Model)

        test_router = RouterBase(
            model=Model,
            crud=crud,
            create_schema=CreateSchema,
            update_schema=UpdateSchema,
            response_schema=ResponseSchema,
            get_db=override_get_db,
            prefix="/items",
            tags=["test"],
        )

        application.include_router(test_router.router)
        return application

    @pytest_asyncio.fixture
    async def client(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    # =========================== CUSTOM FEATURES =========================== #

    async def test_route_exclusion(self, override_get_db):
        """Verify that excluded routes return 405 or 404."""
        app = FastAPI()
        crud = CRUDBase[Model, CreateSchema, UpdateSchema](Model)

        # Exclude 'delete' and 'create'
        test_router = RouterBase(
            model=Model,
            crud=crud,
            create_schema=CreateSchema,
            update_schema=UpdateSchema,
            response_schema=CreateSchema,
            get_db=override_get_db,
            prefix="/restricted",
            exclude_routes=["delete", "create"],
        )
        app.include_router(test_router.router)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Create should fail
            res_post = await client.post("/restricted/", json={"name": "fail"})
            assert res_post.status_code == 405  # Method Not Allowed

            # Get all should still work
            res_get = await client.get("/restricted/")
            assert res_get.status_code == 200

    # =========================== [ HAPPY PATH ] =========================== #

    async def test_router_create(self, client: AsyncClient):
        response = await client.post(
            "/items/", json={"name": "Router Item", "description": "Route test"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Router Item"

    async def test_router_get_all(self, client: AsyncClient):
        for i in range(2):
            await client.post("/items/", json={"name": f"Item {i}"})
        # Get All
        response = await client.get("/items/")
        assert response.status_code == 200
        json = response.json()
        assert json["pagination"]["total"] == 2
        assert len(json["data"]) == 2

    async def test_router_filtering(self, client: AsyncClient):
        for name in ["Target", "Other"]:
            await client.post("/items/", json={"name": name})
        # Filter
        response = await client.get("/items/?name=Target")
        json = response.json()
        data = json["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Target"

    async def test_router_get_one(self, client: AsyncClient):
        res = await client.post("/items/", json={"name": "Find Me"})
        id = res.json()["id"]
        # Get One
        response = await client.get(f"/items/{id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Find Me"

    async def test_router_update(self, client: AsyncClient):
        res = await client.post(
            "/items/", json={"name": "OG", "description": "Keep Me"}
        )
        id = res.json()["id"]
        # Update
        response = await client.patch(f"/items/{id}", json={"name": "Updated"})
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Keep Me"

    async def test_router_delete(self, client: AsyncClient):
        res = await client.post("/items/", json={"name": "Bye Bye"})
        id = res.json()["id"]
        # Delete
        response = await client.delete(f"/items/{id}")
        assert response.status_code == 204, response
        # Verify gone
        check = await client.get(f"/items/{id}")
        assert check.status_code == 404

    async def test_router_pagination(self, client: AsyncClient):
        # Seed 5 items
        for i in range(5):
            await client.post("/items/", json={"name": f"Item {i}"})
        # Test limit
        response = await client.get("/items/?limit=2")
        assert len(response.json()) == 2

    async def test_router_pagination_valid(self, client: AsyncClient):
        # standard allowed limit
        response = await client.get("/items/?limit=50")
        assert response.status_code == 200

    async def test_router_pagination_offset(self, client: AsyncClient):
        for i in range(3):
            await client.post("/items/", json={"name": f"Item {i}"})
        # Skip the first 2, should only return the 3rd
        response = await client.get("/items/?limit=2&page=2")
        json = response.json()
        data = json["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Item 2"

    # ========================== [ UNHAPPY PATH ] ========================== #

    async def test_get_one_not_found(self, client: AsyncClient):
        response = await client.get("/items/9999")
        assert response.status_code == 404

    async def test_create_invalid_data(self, client: AsyncClient):
        response = await client.post("/items/", json={"description": "missing name"})
        assert response.status_code == 422

    async def test_update_non_existent(self, client: AsyncClient):
        response = await client.patch("/items/9999", json={"name": "New"})
        assert response.status_code == 404

    async def test_router_get_all_empty(self, client: AsyncClient):
        # Ensure database is clean
        response = await client.get("/items/")
        assert response.status_code == 200
        json = response.json()
        data = json["data"]
        assert data == []

    async def test_router_pagination_exceeds_limit(self, client: AsyncClient):
        # INTENT: Big Query Attack
        response = await client.get("/items/?limit=10000")
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("limit" in err["loc"] for err in errors)

    async def test_router_ignore_invalid_filters(self, client: AsyncClient):
        response = await client.get("/items/?fake_field=value")
        assert response.status_code == 200  # ignore (200) or 422, but never 500

    async def test_router_pagination_out_of_bounds_page(self, client: AsyncClient):
        response = await client.get("/items/?limit=10&page=999")
        assert response.status_code == 200
        json = response.json()
        data = json["data"]
        assert data == []

    async def test_router_pagination_invalid_page(self, client: AsyncClient):
        response = await client.get("/items/?page=0")
        assert response.status_code == 422
