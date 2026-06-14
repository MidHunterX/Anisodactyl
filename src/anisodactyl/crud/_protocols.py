from typing import (Any, Callable, Optional, Protocol, Sequence, Type, TypeVar,
                    runtime_checkable)

from pydantic import BaseModel
from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing_extensions import Dict

from anisodactyl.query.base import FilterDict

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel, contravariant=True)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel, contravariant=True)
JSONType = dict[str, Any]


@runtime_checkable
class CRUDProtocol(Protocol[ModelType, CreateSchemaType, UpdateSchemaType]):
    model: Type[ModelType]
    _operators: Dict[str, Callable[[Any, Any], ColumnElement]]

    async def get(self, db: AsyncSession, **kwargs) -> Optional[ModelType]: ...

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[list[FilterDict]] = None,
        **kwargs,
    ) -> Sequence[ModelType]: ...

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType, auto_commit: bool = True,
    ) -> ModelType: ...

    async def update(
        self,
        db: AsyncSession,
        *,
        db_model: ModelType,
        obj_in: UpdateSchemaType | JSONType,
        auto_commit: bool = True,
    ) -> ModelType: ...

    async def remove(
        self, db: AsyncSession, *, auto_commit: bool = True, **kwargs
    ) -> Optional[ModelType]: ...
