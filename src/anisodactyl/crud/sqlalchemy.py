from typing import Any, Callable, Dict, Sequence, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase, load_only

from ._protocols import CRUDProtocol

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(
    CRUDProtocol[ModelType, CreateSchemaType, UpdateSchemaType, AsyncSession]
):
    def __init__(
        self,
        model,
        *,
        child_models: dict[str, Type[DeclarativeBase]] | None = None,
    ):
        self.model = model
        self.child_models = child_models or {}

        # CHECK: Validate child model config
        mapper = inspect(self.model)
        for rel_name, child_model in self.child_models.items():
            if rel_name not in mapper.relationships:
                raise ValueError(
                    f"CONFIG ERROR: Relationship '{rel_name}' does not exist on model '{self.model.__name__}'"
                )
            rel = mapper.relationships[rel_name]
            if rel.mapper.class_ != child_model:
                raise ValueError(
                    f"CONFIG ERROR: Relationship '{rel_name}' target class '{rel.mapper.class_.__name__}'"
                    f"does not match provided child model '{child_model.__name__}'"
                )

        self._operators: Dict[str, Callable[[Any, Any], ColumnElement]] = {
            # Numeric / Basic
            "eq": lambda field, val: field == val,
            "ne": lambda field, val: field != val,
            "gt": lambda field, val: field > val,
            "lt": lambda field, val: field < val,
            "gte": lambda field, val: field >= val,
            "lte": lambda field, val: field <= val,
            # String Pattern Matching
            # ilike by default as urls are case insensitive
            "contains": lambda field, val: field.ilike(f"%{val}%"),
            "startswith": lambda field, val: field.ilike(f"{val}%"),
            "endswith": lambda field, val: field.ilike(f"%{val}"),
            "like": lambda field, val: field.ilike(val),
            # List
            # might attack with ?status=in:active,pending,hidden_status overriding API logic
            # "in": lambda field, val: field.in_(val if isinstance(val, list) else [val]),
            # "nin": lambda field, val: ~field.in_(val if isinstance(val, list) else [val]),
            # Null check
            # No need for frontend to do null checks. Should be done by backend
            # "isnull": lambda field, val: field.is_(None) if str(val).lower() != "false" else field.is_not(None),
            # "notnull": lambda field, val: field.is_not(None) if str(val).lower() != "false" else field.is_(None),
            # Ranges
            "between": lambda field, val: (
                field.between(val[0], val[1])
                if isinstance(val, list) and len(val) == 2
                else field == val
            ),
        }

    async def get(self, db, **kwargs):
        """Usage: `crud.get(db, id=1)` OR `crud.get(db, email="test@test.com")`"""
        if not kwargs:  # Prevent full table query
            raise ValueError("At least one filter is required (db, id=1).")
        query = select(self.model).filter_by(**kwargs)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db, skip=0, limit=100, filters=None, sort=None, fields=None, **kwargs
    ) -> tuple[Sequence[ModelType], int]:
        """
        Backend Usage: `crud.get_multi(db, email="test@test.com")`
        JSON Usage: `crud.get_multi(db, filters=[{"field": "email", "op": "eq", "value": "test@test.com"}])`
        """
        query = select(self.model)

        if fields:
            valid_fields = []
            for field_name in fields:
                if hasattr(self.model, field_name):
                    valid_fields.append(getattr(self.model, field_name))
            if valid_fields:
                query = query.options(load_only(*valid_fields))

        if filters:
            for f in filters:
                field = getattr(self.model, f["field"], None)
                operator = f["op"]
                value = f["value"]
                if field is not None and operator in self._operators:
                    # Handle between operator
                    if operator == "between":
                        if isinstance(value, str) and "," in value:
                            value = value.split(",", 1)
                        if not isinstance(value, (list, tuple)) or len(value) != 2:
                            continue
                    query = query.where(self._operators[operator](field, value))

        if sort:
            for sort_field in sort:
                if sort_field.startswith("-"):
                    field_name = sort_field[1:]
                    descending = True
                else:
                    field_name = sort_field
                    descending = False
                field_attr = getattr(self.model, field_name, None)
                if field_attr is not None:
                    if descending:
                        query = query.order_by(field_attr.desc())
                    else:
                        query = query.order_by(field_attr.asc())

        # kwargs filtering for Backend
        if kwargs:
            query = query.filter_by(**kwargs)

        # Pagination Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all(), total_count

    async def create(self, db, *, obj_in, auto_commit=True) -> ModelType:
        obj_data = obj_in.copy() if isinstance(obj_in, dict) else obj_in.model_dump()

        # EXTRACT: Children
        child_data: dict[str, Any] = {}
        for rel_name in self.child_models:
            if rel_name in obj_data:
                child_data[rel_name] = obj_data.pop(rel_name)

        # ACTION: Create Current
        db_obj = self.model(**obj_data)

        # ACTION: Create Children
        parent_mapper = inspect(self.model)
        for rel_name, items in child_data.items():
            if items is None:
                continue
            child_model = self.child_models[rel_name]
            is_list = parent_mapper.relationships[rel_name].uselist
            if is_list:
                if not isinstance(items, list):
                    raise ValueError(f"Expected a list for relationship '{rel_name}'")
                children = [child_model(**item) for item in items]
                setattr(db_obj, rel_name, children)
            else:
                if not isinstance(items, dict):
                    raise ValueError(
                        f"Expected a dictionary for relationship '{rel_name}'"
                    )
                child = child_model(**items)
                setattr(db_obj, rel_name, child)

        return await self._save(db, db_obj, auto_commit)

    # Why does this need db_model?
    # update() does what it is responsible for.
    # you can instead get creative on get() using kwargs filtering
    async def update(self, db, *, db_model, obj_in, auto_commit=True) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # EXTRACT: Children
        child_data: dict[str, Any] = {}
        for rel_name in self.child_models:
            if rel_name in update_data:
                child_data[rel_name] = update_data.pop(rel_name)

        # ACTION: Update Current
        for field, value in update_data.items():
            if hasattr(db_model, field):
                setattr(db_model, field, value)

        # ACTION: Update/Create nested Children
        if child_data:
            parent_mapper = inspect(self.model)
            # Important: Pre-load unloaded relationships mapped in this request to avoid
            # sqlalchemy.exc.MissingGreenletError when using AsyncSession
            unloaded_rels = inspect(db_model).unloaded
            rels_to_load = [rel for rel in child_data.keys() if rel in unloaded_rels]
            if rels_to_load:
                await db.refresh(db_model, attribute_names=rels_to_load)

            for rel_name, items in child_data.items():
                if items is None:
                    continue
                child_model = self.child_models[rel_name]
                is_list = parent_mapper.relationships[rel_name].uselist
                # Get PK column name of the child model
                child_pk_name = inspect(child_model).primary_key[0].name

                if is_list:
                    # 1-N relationship
                    if not isinstance(items, list):
                        raise ValueError(
                            f"Expected a list for relationship '{rel_name}'"
                        )
                    existing_children_list = getattr(db_model, rel_name)
                    existing_children_map = {
                        str(getattr(c, child_pk_name)): c
                        for c in existing_children_list
                        if getattr(c, child_pk_name) is not None
                    }
                    for item_data in items:
                        item_pk = item_data.get(child_pk_name)
                        # if child.pk: update else create
                        if item_pk and str(item_pk) in existing_children_map:
                            child_obj = existing_children_map[str(item_pk)]
                            for k, v in item_data.items():
                                if hasattr(child_obj, k):
                                    setattr(child_obj, k, v)
                        else:
                            new_child = child_model(**item_data)
                            existing_children_list.append(new_child)
                else:
                    # 1-1 relationship
                    if not isinstance(items, dict):
                        raise ValueError(
                            f"Expected a dictionary for relationship '{rel_name}'"
                        )
                    this_child = getattr(db_model, rel_name)
                    item_pk = items.get(child_pk_name)
                    is_update = str(getattr(this_child, child_pk_name)) == str(item_pk)
                    if this_child and item_pk and is_update:
                        # Update existing scalar child
                        for k, v in items.items():
                            if hasattr(this_child, k):
                                setattr(this_child, k, v)
                    else:
                        # Create and assign new scalar child
                        new_child = child_model(**items)
                        setattr(db_model, rel_name, new_child)

        return await self._save(db, db_model, auto_commit)

    async def remove(self, db, *, auto_commit=True, **kwargs) -> ModelType | None:
        """Usage: `crud.remove(db, id=1)` OR `crud.remove(db, email="test@test.com")`"""
        query = select(self.model).filter_by(**kwargs)
        result = await db.execute(query)
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            if auto_commit:
                await db.commit()
            else:
                await db.flush()
        return obj

    async def _save(
        self, db: AsyncSession, model: ModelType, auto_commit: bool
    ) -> ModelType:
        db.add(model)
        if auto_commit:
            await db.commit()
            await db.refresh(model)
            if self.child_models:
                await db.refresh(model, attribute_names=list(self.child_models.keys()))
        else:
            await db.flush()
        return model
