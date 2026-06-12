from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
JSONType = dict[str, Any]


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """Usage: `crud.get(db, id=1)` OR `crud.get(db, email="test@test.com")`"""
        if not kwargs:  # Prevent full table query
            raise ValueError("At least one filter is required (db, id=1).")
        query = select(self.model).filter_by(**kwargs)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, **kwargs
    ) -> Sequence[ModelType]:
        query = select(self.model).filter_by(**kwargs).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType, auto_commit: bool = True
    ) -> ModelType:
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        return await self._save(db, db_obj, auto_commit)

    # Why does this need db_model?
    # update() does what it is responsible for.
    # you can instead get creative on get() using kwargs filtering
    async def update(
        self,
        db: AsyncSession,
        *,
        db_model: ModelType,
        obj_in: UpdateSchemaType | JSONType,
        auto_commit: bool = True,
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_model, field):
                setattr(db_model, field, update_data[field])

        return await self._save(db, db_model, auto_commit)

    async def remove(
        self, db: AsyncSession, *, auto_commit: bool = True, **kwargs
    ) -> Optional[ModelType]:
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
