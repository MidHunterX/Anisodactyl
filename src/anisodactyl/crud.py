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
        query = select(self.model).filter_by(**kwargs)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, **kwargs
    ) -> Sequence[ModelType]:
        query = select(self.model).filter_by(**kwargs).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_model: ModelType,
        obj_in: UpdateSchemaType | JSONType,
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_model, field):
                setattr(db_model, field, update_data[field])

        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)
        return db_model

    async def remove(self, db: AsyncSession, **kwargs) -> Optional[ModelType]:
        """Usage: `crud.remove(db, id=1)` OR `crud.remove(db, email="test@test.com")`"""
        query = select(self.model).filter_by(**kwargs)
        result = await db.execute(query)
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
