from typing import (Any, Optional, Protocol, Sequence, Type, TypeVar,
                    runtime_checkable)

from pydantic import BaseModel  # Tightly coupled as it is the standard
from typing_extensions import TypedDict

SessionType = TypeVar("SessionType", contravariant=True)
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel, contravariant=True)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel, contravariant=True)
JSONType = dict[str, Any]


class FilterDict(TypedDict):
    field: str
    op: str
    value: Any


@runtime_checkable
class CRUDProtocol(
    Protocol[ModelType, CreateSchemaType, UpdateSchemaType, SessionType]
):
    def __init__(self, model: Type[ModelType]): ...

    async def get(self, db: SessionType, **kwargs) -> Optional[ModelType]: ...

    async def get_multi(
        self,
        db: SessionType,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[list[FilterDict]] = None,
        sort: Optional[list[str]] = None,
        fields: Optional[list[str]] = None,
        **kwargs,
    ) -> tuple[Sequence[ModelType], int]: ...

    async def create(
        self,
        db: SessionType,
        *,
        obj_in: CreateSchemaType,
        auto_commit: bool = True,
    ) -> ModelType: ...

    async def update(
        self,
        db: SessionType,
        *,
        db_model: ModelType,
        obj_in: UpdateSchemaType | JSONType,
        auto_commit: bool = True,
    ) -> ModelType: ...

    async def remove(
        self, db: SessionType, *, auto_commit: bool = True, **kwargs
    ) -> Optional[ModelType]: ...
