import pytest
import pytest_asyncio
from conftest import CreateSchema, Model, UpdateSchema
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from anisodactyl import CRUDBase, RouterBase


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
            response_schema=CreateSchema,
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

    async def test_router_create(self, client: AsyncClient):
        response = await client.post(
            "/items/", json={"name": "Router Item", "description": "Route test"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Router Item"

    async def test_router_get_all(self, client: AsyncClient, db_session):
        # Seed data
        crud = CRUDBase(Model)
        await crud.create(db_session, obj_in=CreateSchema(name="Item A"))
        await crud.create(db_session, obj_in=CreateSchema(name="Item B"))

        response = await client.get("/items/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_router_filtering(self, client: AsyncClient, db_session):
        # Seed data
        crud = CRUDBase(Model)
        await crud.create(db_session, obj_in=CreateSchema(name="Target"))
        await crud.create(db_session, obj_in=CreateSchema(name="Other"))

        # Test filter
        response = await client.get("/items/?name=Target")
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Target"

    async def test_router_get_one(self, client: AsyncClient, db_session):
        crud = CRUDBase(Model)
        obj = await crud.create(db_session, obj_in=CreateSchema(name="Find Me"))

        response = await client.get(f"/items/{obj.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Find Me"

    async def test_router_update(self, client: AsyncClient, db_session):
        crud = CRUDBase(Model)
        obj = await crud.create(db_session, obj_in=CreateSchema(name="Old Name"))

        response = await client.patch(f"/items/{obj.id}", json={"name": "New Name"})
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_router_delete(self, client: AsyncClient, db_session):
        crud = CRUDBase(Model)
        obj = await crud.create(db_session, obj_in=CreateSchema(name="Bye Bye"))

        response = await client.delete(f"/items/{obj.id}")
        assert response.status_code == 204

        # Verify gone
        check = await client.get(f"/items/{obj.id}")
        assert check.status_code == 404

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
        ) as ac:
            # Create should fail
            res_post = await ac.post("/restricted/", json={"name": "fail"})
            assert res_post.status_code == 405  # Method Not Allowed

            # Get all should still work
            res_get = await ac.get("/restricted/")
            assert res_get.status_code == 200
