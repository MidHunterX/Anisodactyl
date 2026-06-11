import pytest
from conftest import CreateSchema, Model, UpdateSchema

from anisodactyl.crud import CRUDBase


@pytest.mark.asyncio
class TestCRUDBase:

    @pytest.fixture
    def crud(self, test_model):
        return CRUDBase[Model, CreateSchema, UpdateSchema](test_model)

    async def test_create(self, db_session, crud):
        obj_in = CreateSchema(name="Test Item", description="Test Description")
        db_obj = await crud.create(db_session, obj_in=obj_in)

        assert db_obj.id is not None
        assert db_obj.name == "Test Item"
        assert db_obj.description == "Test Description"

    async def test_get(self, db_session, crud):
        # Create an object first
        obj_in = CreateSchema(name="Fetch Me")
        created_obj = await crud.create(db_session, obj_in=obj_in)

        # Test retrieval
        fetched_obj = await crud.get(db_session, id=created_obj.id)
        assert fetched_obj is not None
        assert fetched_obj.id == created_obj.id
        assert fetched_obj.name == "Fetch Me"

    async def test_get_multi(self, db_session, crud):
        # Create multiple objects
        await crud.create(db_session, obj_in=CreateSchema(name="Item 1"))
        await crud.create(db_session, obj_in=CreateSchema(name="Item 2"))
        await crud.create(db_session, obj_in=CreateSchema(name="Item 3"))

        # Test limit
        objs = await crud.get_multi(db_session, skip=0, limit=2)
        assert len(objs) == 2

        # Test skip
        objs_skipped = await crud.get_multi(db_session, skip=2, limit=2)
        assert len(objs_skipped) == 1

    async def test_update_with_schema(self, db_session, crud):
        # Create
        db_obj = await crud.create(db_session, obj_in=CreateSchema(name="Old Name"))

        # Update using Schema
        update_data = UpdateSchema(name="New Name")
        updated_obj = await crud.update(db_session, db_model=db_obj, obj_in=update_data)

        assert updated_obj.name == "New Name"
        assert updated_obj.id == db_obj.id

    async def test_update_with_dict(self, db_session, crud):
        # Create
        db_obj = await crud.create(db_session, obj_in=CreateSchema(name="Old Name"))

        # Update using Dict
        update_data = {"name": "Dict Name"}
        updated_obj = await crud.update(db_session, db_model=db_obj, obj_in=update_data)

        assert updated_obj.name == "Dict Name"

    async def test_remove(self, db_session, crud):
        # Create
        db_obj = await crud.create(db_session, obj_in=CreateSchema(name="Delete Me"))
        obj_id = db_obj.id

        # Remove
        removed_obj = await crud.remove(db_session, id=obj_id)
        assert removed_obj is not None
        assert removed_obj.id == obj_id

        # Verify removal
        found_obj = await crud.get(db_session, id=obj_id)
        assert found_obj is None

    async def test_get_non_existent(self, db_session, crud):
        obj = await crud.get(db_session, id=999)
        assert obj is None
