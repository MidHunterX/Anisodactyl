import pytest
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from anisodactyl.crud.sqlalchemy import CRUDBase
from tests.app.models import (ChildModel, ChildModel2, ContactModel, Model,
                              ParentModel)
from tests.app.schemas import ChildCreateSchema, CreateSchema, UpdateSchema


@pytest.mark.asyncio
class TestCRUDBaseMutant:

    @pytest.fixture
    def crud_with_children(self):
        return CRUDBase[Model, CreateSchema, UpdateSchema](
            Model,
            child_models={
                "child": ChildModel,
                "child2": ChildModel2,
                "contacts": ContactModel,
            },
        )

    async def test_init_validation_failure(self):
        # Relationship name doesn't exist
        with pytest.raises(ValueError, match="does not exist on model"):
            CRUDBase(Model, child_models={"invalid_relation": ChildModel})

        # Relationship target model doesn't match
        with pytest.raises(ValueError, match="does not match provided child model"):
            CRUDBase(Model, child_models={"child": ParentModel})

    async def test_create_with_nested_scalar_and_list(
        self, db_session: AsyncSession, crud_with_children: CRUDBase
    ):
        obj_in = {
            "name": "Main Model",
            "child": {"name": "Scalar Child"},
            "contacts": [
                {"name": "Email", "value": "test@example.com"},
                {"name": "Phone", "value": "123456"},
            ],
        }

        db_obj = await crud_with_children.create(db_session, obj_in=obj_in)

        assert db_obj.id is not None
        assert db_obj.child.name == "Scalar Child"
        assert len(db_obj.contacts) == 2
        assert db_obj.contacts[0].id is not None

    async def test_update_collection_syncing(
        self, db_session: AsyncSession, crud_with_children: CRUDBase
    ):
        # Setup: One parent one contact
        db_obj = await crud_with_children.create(
            db_session,
            obj_in={
                "name": "Parent",
                "contacts": [{"name": "Old", "value": "old@test.com"}],
            },
        )
        old_contact_id = db_obj.contacts[0].id

        # Update:
        # Contact 1: Has ID -> Should Update
        # Contact 2: No ID -> Should Create
        update_data = {
            "contacts": [
                {
                    "id": old_contact_id,
                    "name": "Updated Name",
                    "value": "updated@test.com",
                },
                {"name": "New Contact", "value": "new@test.com"},
            ]
        }

        updated_obj = await crud_with_children.update(
            db_session, db_model=db_obj, obj_in=update_data
        )

        assert len(updated_obj.contacts) == 2

        # Verify update
        updated_contact = next(
            c for c in updated_obj.contacts if c.id == old_contact_id
        )
        assert updated_contact.name == "Updated Name"

        # Verify creation
        new_contact = next(c for c in updated_obj.contacts if c.id != old_contact_id)
        assert new_contact.name == "New Contact"

    async def test_update_scalar_child_identity(
        self, db_session: AsyncSession, crud_with_children: CRUDBase
    ):
        # Create with child
        db_obj = await crud_with_children.create(
            db_session, obj_in={"name": "Parent", "child": {"name": "C1"}}
        )
        original_child_id = db_obj.child.id

        # Update scalar without ID -> Creates new object and replaces link
        # (This is standard SQLAlchemy behavior for 1:1 if you don't provide the PK)
        update_data = {"child": {"name": "New C1"}}
        updated_obj = await crud_with_children.update(
            db_session, db_model=db_obj, obj_in=update_data
        )

        assert updated_obj.child.id != original_child_id
        assert updated_obj.child.name == "New C1"

    async def test_create_via_pydantic_schema(
        self, db_session: AsyncSession, crud_with_children: CRUDBase
    ):
        # Test passing the actual Schema object instead of dict
        schema_in = CreateSchema(
            name="Schema Parent", child=ChildCreateSchema(name="Schema Child")
        )

        db_obj = await crud_with_children.create(db_session, obj_in=schema_in)
        assert db_obj.name == "Schema Parent"
        assert db_obj.child.name == "Schema Child"

    async def test_update_ignores_unrelated_fields(
        self, db_session: AsyncSession, crud_with_children: CRUDBase
    ):
        db_obj = await crud_with_children.create(db_session, obj_in={"name": "Test"})

        # "random_field" is not on the model. Should not crash.
        update_data = {"name": "New Name", "random_field": "ignore_me"}
        updated_obj = await crud_with_children.update(
            db_session, db_model=db_obj, obj_in=update_data
        )

        assert updated_obj.name == "New Name"

    async def test_multi_nested_creation_single_transaction(
        self, db_session: AsyncSession, crud_with_children: CRUDBase
    ):
        async with db_session.begin():
            # Create first parent with a collection of children
            await crud_with_children.create(
                db_session,
                obj_in={
                    "name": "Transaction Parent 1",
                    "contacts": [
                        {"name": "Home", "value": "123"},
                        {"name": "Work", "value": "456"},
                    ],
                },
                auto_commit=False,
            )

            # Create second parent with a scalar child
            await crud_with_children.create(
                db_session,
                obj_in={
                    "name": "Transaction Parent 2",
                    "child": {"name": "Nested Child"},
                },
                auto_commit=False,
            )

        # Transaction commits here when block exits.
        # Now verify both exist and children are correctly linked.
        items, count = await crud_with_children.get_multi(db_session, sort=["name"])

        assert count == 2

        # Verify P1
        p1 = items[0]
        assert p1.name == "Transaction Parent 1"
        await db_session.refresh(p1, ["contacts"])
        assert len(p1.contacts) == 2

        # Verify P2
        p2 = items[1]
        assert p2.name == "Transaction Parent 2"
        await db_session.refresh(p2, ["child"])
        assert p2.child.name == "Nested Child"

    async def test_nested_creation_rollback(
        self, db_session: AsyncSession, crud_with_children: CRUDBase
    ):
        try:
            async with db_session.begin():
                # Stage a complex object
                await crud_with_children.create(
                    db_session,
                    obj_in={
                        "name": "I should not exist",
                        "child": {"name": "Temporary Child"},
                        "contacts": [{"name": "Temp", "value": "Temp"}],
                    },
                    auto_commit=False,
                )
                # Force an error
                raise RuntimeError("Simulated Transaction Failure")
        except RuntimeError:
            pass

        # Verify parent table is empty
        _, count = await crud_with_children.get_multi(db_session)
        assert count == 0

        # Verify child tables are also empty (integrity check)
        from sqlalchemy import select

        from tests.app.models import ChildModel, ContactModel

        child_count = await db_session.execute(
            select(func.count()).select_from(ChildModel)
        )
        contact_count = await db_session.execute(
            select(func.count()).select_from(ContactModel)
        )

        assert child_count.scalar() == 0
        assert contact_count.scalar() == 0
