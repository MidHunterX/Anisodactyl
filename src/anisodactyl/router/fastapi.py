from enum import Enum
from typing import Any, Generic, List, Type, TypeVar

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing_extensions import Literal

from anisodactyl.query.base import QueryParserProtocol
from anisodactyl.query.sqlalchemy import QueryParams

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
        # CRUD PARAMETERS
        # ===============
        model: Type[ModelType],
        crud: Any, # TODO: Add typing
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
        get_db: Any,  # session dependency
        query_parser: Type[QueryParserProtocol] = QueryParams,
        # APIROUTER PARAMETERS
        # ====================
        prefix: str,
        tags: List[str | Enum] | None = None,
    ):
        self.model = model
        self.crud = crud
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.get_db = get_db
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.query_parser = query_parser
        self._register_routes()

    def _register_routes(self):
        @self.router.get("/", response_model=List[self.response_schema])
        async def get_all(
            db: AsyncSession = Depends(self.get_db),
            params: QueryParserProtocol = Depends(self.query_parser),
            limit: int = 100,
            offset: int = 0,
        ):
            return await self.crud.get_multi(
                db, filters=params.filters, limit=limit, offset=offset
            )

    async def get_router(self) -> APIRouter:
        return self.router
