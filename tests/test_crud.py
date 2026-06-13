import pytest
from conftest import CreateSchema, Model, UpdateSchema
from sqlalchemy.ext.asyncio import AsyncSession

from anisodactyl import CRUDBase


@pytest.mark.asyncio
class TestCRUDBase:
    # Why class for test?
    # pytest doesn't natively support async testing.
    # We use pytest-asyncio. It need decorator on top of tests.
    # The best way to do is: Group tests in class. Add decorator to class.

    @pytest.fixture
    def crud(self):
        return CRUDBase[Model, CreateSchema, UpdateSchema](Model)

    async def test_create(self, db_session, crud: CRUDBase):
        obj_in = CreateSchema(name="Test Item", description="Test Description")
        db_obj = await crud.create(db_session, obj_in=obj_in)

        assert db_obj.id is not None
        assert db_obj.name == "Test Item"
        assert db_obj.description == "Test Description"

    async def test_transaction_pass(self, db_session: AsyncSession, crud: CRUDBase):
        async with db_session.begin():
            await crud.create(
                db_session,
                obj_in=CreateSchema(name="Test Item"),
                auto_commit=False,
            )
            await crud.create(
                db_session,
                obj_in=CreateSchema(name="Test Item 2"),
                auto_commit=False,
            )
            await crud.create(
                db_session,
                obj_in=CreateSchema(name="Test Item 3"),
                auto_commit=False,
            )

        objs = await crud.get_multi(db_session)
        assert len(objs) == 3

    async def test_transaction_fail(self, db_session: AsyncSession, crud: CRUDBase):
        with pytest.raises(Exception):
            async with db_session.begin():
                obj = await crud.create(
                    db_session,
                    obj_in=CreateSchema(name="Test Item"),
                    auto_commit=False,
                )
                await crud.update(
                    db_session,
                    db_model=obj,
                    obj_in=CreateSchema(name="Test Item 2"),
                    auto_commit=False,
                )
                raise Exception

        objs = await crud.get_multi(db_session)
        assert len(objs) == 0

    async def test_get(self, db_session, crud: CRUDBase):
        # Create an object first
        obj_in = CreateSchema(name="Fetch Me")
        created_obj = await crud.create(db_session, obj_in=obj_in)

        # Test retrieval
        fetched_obj = await crud.get(db_session, id=created_obj.id)
        assert fetched_obj is not None
        assert fetched_obj.id == created_obj.id
        assert fetched_obj.name == "Fetch Me"

        # Test filters
        obj_filtered = await crud.get(db_session, name="Fetch Me", id=1)
        assert obj_filtered is not None
        obj_filtered = await crud.get(db_session, name="No Fetch Me")
        assert obj_filtered is None

    async def test_get_multi(self, db_session, crud: CRUDBase):
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

        # Test filters
        objs_filtered = await crud.get_multi(db_session, name="Item 2", id=2)
        assert len(objs_filtered) == 1

    async def test_update_with_schema(self, db_session, crud: CRUDBase):
        # Create
        db_obj = await crud.create(db_session, obj_in=CreateSchema(name="Old Name"))

        # Update using Schema
        update_data = UpdateSchema(name="New Name")
        updated_obj = await crud.update(db_session, db_model=db_obj, obj_in=update_data)

        assert updated_obj.name == "New Name"
        assert updated_obj.id == db_obj.id

    async def test_update_with_dict(self, db_session, crud: CRUDBase):
        # Create
        db_obj = await crud.create(db_session, obj_in=CreateSchema(name="Old Name"))

        # Update using Dict
        update_data = {"name": "Dict Name"}
        updated_obj = await crud.update(db_session, db_model=db_obj, obj_in=update_data)

        assert updated_obj.name == "Dict Name"

    async def test_remove(self, db_session, crud: CRUDBase):
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

    async def test_get_non_existent(self, db_session, crud: CRUDBase):
        obj = await crud.get(db_session, id=999)
        assert obj is None
