from enum import Enum
from typing import Any, Generic, List, Type, TypeVar

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from typing_extensions import Literal

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
JSONType = dict[str, Any]
RouteNames = Literal["get", "get_all", "create", "update", "delete"]


class RouterBase(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]
):
    def __init__(
        self,
        *,
        # REQUIRED PARAMETERS
        # ===================
        model: Type[ModelType],
        prefix: str,
        # OPTIONAL PARAMETERS
        # ===================
        tags: List[str | Enum] | None,
    ):
        self.model = model
        self.router = APIRouter(prefix=prefix, tags=tags)

    async def get_router(self) -> APIRouter:
        return self.router
