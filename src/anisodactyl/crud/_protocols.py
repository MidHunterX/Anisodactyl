from typing import (Any, Optional, Protocol, Sequence, Type, TypeVar,
                    runtime_checkable)

from typing_extensions import TypedDict

SessionType = TypeVar("SessionType", contravariant=True)
ModelType = TypeVar("ModelType")
ChildModelType = type[Any] # Tell via LSP that it's supposed to be a child and not just any

JSONType = dict[str, Any]
CreateSchemaType = TypeVar("CreateSchemaType", contravariant=True)
UpdateSchemaType = TypeVar("UpdateSchemaType", contravariant=True)


class FilterDict(TypedDict):
    field: str
    op: str
    value: Any


@runtime_checkable
class CRUDProtocol(
    Protocol[ModelType, CreateSchemaType, UpdateSchemaType, SessionType]
):
    def __init__(
        self,
        model: Type[ModelType],
        *,
        # NOTE: Make sure to narrow down type of child_models with ORM class on
        # implementation for LSP autocompletion when developing
        child_models: Optional[dict[str, ChildModelType]] = None,
    ): ...

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
        obj_in: CreateSchemaType | JSONType,
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
