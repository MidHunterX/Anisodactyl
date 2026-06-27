from typing import List, Optional

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from anisodactyl.crud.sqlalchemy import CRUDBase
from anisodactyl.router.fastapi import RouterBase
from tests.app.models import ChildModel, ContactModel, Model
from tests.app.schemas import ChildCreateSchema


class ContactSchema(BaseModel):
    id: Optional[int] = None
    name: str
    value: str


class NestedCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    child: Optional[ChildCreateSchema] = None
    contacts: Optional[List[ContactSchema]] = None


class NestedUpdateSchema(BaseModel):
    name: Optional[str] = None
    child: Optional[ChildCreateSchema] = None
    contacts: Optional[List[ContactSchema]] = None


class NestedResponseSchema(BaseModel):
    id: int
    name: str
    child: Optional[ChildCreateSchema] = None
    contacts: List[ContactSchema] = []


@pytest.mark.asyncio
class TestRouterMutation:

    @pytest.fixture
    def app(self, override_get_db):
        """Temp FastAPI app for nested router testing"""
        application = FastAPI()

        crud = CRUDBase[Model, NestedCreateSchema, NestedUpdateSchema](
            Model,
            child_models={
                "child": ChildModel,
                "contacts": ContactModel,
            },
        )

        test_router = RouterBase(
            model=Model,
            crud=crud,
            create_schema=NestedCreateSchema,
            update_schema=NestedUpdateSchema,
            response_schema=NestedResponseSchema,
            get_db=override_get_db,
            prefix="/items",
        )

        application.include_router(test_router.router)
        return application

    @pytest_asyncio.fixture
    async def client(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    async def test_router_create_nested(self, client: AsyncClient):
        """Verify POST /items/ creates parent and children simultaneously."""
        payload = {
            "name": "Parent API",
            "child": {"name": "Child API"},
            "contacts": [{"name": "Email", "value": "api@test.com"}],
        }
        response = await client.post("/items/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Parent API"
        assert data["child"]["name"] == "Child API"
        assert len(data["contacts"]) == 1
        assert data["contacts"][0]["value"] == "api@test.com"

    async def test_router_update_nested_sync(self, client: AsyncClient):
        """Verify PATCH /items/{id} updates existing children and creates new ones."""
        setup_res = await client.post(
            "/items/",
            json={"name": "Initial", "contacts": [{"name": "C1", "value": "v1"}]},
        )
        parent_id = setup_res.json()["id"]
        contact_id = setup_res.json()["contacts"][0]["id"]

        update_payload = {
            "contacts": [
                {"id": contact_id, "name": "C1-Updated", "value": "v1-new"},
                {"name": "C2-New", "value": "v2"},
            ]
        }

        response = await client.patch(f"/items/{parent_id}", json=update_payload)
        assert response.status_code == 200

        data = response.json()
        assert len(data["contacts"]) == 2

        c1 = next(c for c in data["contacts"] if c["id"] == contact_id)
        assert c1["name"] == "C1-Updated"

        c2 = next(c for c in data["contacts"] if c["id"] != contact_id)
        assert c2["name"] == "C2-New"

    async def test_router_scalar_child_replacement(self, client: AsyncClient):
        """Verify that updating a scalar child without ID creates a new record."""
        setup_res = await client.post(
            "/items/", json={"name": "Parent", "child": {"name": "Old Child"}}
        )
        parent_id = setup_res.json()["id"]

        response = await client.patch(
            f"/items/{parent_id}", json={"child": {"name": "Brand New Child"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["child"]["name"] == "Brand New Child"

    async def test_router_validation_error_nested(self, client: AsyncClient):
        """Verify that Pydantic validation still works for nested structures."""
        bad_payload = {"name": "Bad", "contacts": "not-a-list"}
        response = await client.post("/items/", json=bad_payload)
        assert response.status_code == 422

    async def test_router_partial_update_ignores_missing_children(
        self, client: AsyncClient
    ):
        """Verify that if children aren't in the PATCH payload, they aren't touched/deleted."""
        setup_res = await client.post(
            "/items/", json={"name": "Parent", "child": {"name": "Keep Me"}}
        )
        parent_id = setup_res.json()["id"]

        response = await client.patch(
            f"/items/{parent_id}", json={"name": "New Parent Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Parent Name"
        # The child should still be there
        assert data["child"]["name"] == "Keep Me"
