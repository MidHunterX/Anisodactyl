from typing import Any, Callable, Dict, Optional, Sequence, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, load_only

from ._protocols import CRUDProtocol

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
JSONType = dict[str, Any]


class CRUDBase(CRUDProtocol[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model):
        self.model = model

        self._operators: Dict[str, Callable[[Any, Any], ColumnElement]] = {
            "eq": lambda field, val: field == val,
            "ne": lambda field, val: field != val,
            "gt": lambda field, val: field > val,
            "lt": lambda field, val: field < val,
            "gte": lambda field, val: field >= val,
            "lte": lambda field, val: field <= val,
            "contains": lambda field, val: field.ilike(f"%{val}%"),
            "startswith": lambda field, val: field.ilike(f"{val}%"),
            "endswith": lambda field, val: field.ilike(f"%{val}"),
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
    ) -> Sequence[ModelType]:
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

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db, *, obj_in, auto_commit=True) -> ModelType:
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        return await self._save(db, db_obj, auto_commit)

    # Why does this need db_model?
    # update() does what it is responsible for.
    # you can instead get creative on get() using kwargs filtering
    async def update(self, db, *, db_model, obj_in, auto_commit=True) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_model, field):
                setattr(db_model, field, update_data[field])

        return await self._save(db, db_model, auto_commit)

    async def remove(self, db, *, auto_commit=True, **kwargs) -> Optional[ModelType]:
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
        else:
            await db.flush()
        return model
