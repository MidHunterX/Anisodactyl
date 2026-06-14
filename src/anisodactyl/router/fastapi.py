from enum import Enum
from typing import Any, Generic, List, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing_extensions import Literal

from anisodactyl.crud.base import CRUDProtocol
from anisodactyl.query.anisodactyl import QueryParams  # Default Query Parser
from anisodactyl.query.base import QueryParserProtocol

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
        crud: CRUDProtocol,
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
        self._register_getall_route()
        self._register_getone_route()
        self._register_create_route()
        self._register_update_route()
        self._register_delete_route()

    def _register_getall_route(self):
        @self.router.get("/", response_model=List[self.response_schema])
        async def get_all(
            db: AsyncSession = Depends(self.get_db),
            params: QueryParserProtocol = Depends(self.query_parser),
            limit: int = 100,
            offset: int = 0,
        ):
            return await self.crud.get_multi(
                db=db,
                skip=offset,
                limit=limit,
                filters=params.filters,
                sort=params.sort,
                fields=params.fields,
            )

    def _register_getone_route(self):
        @self.router.get("/{id}", response_model=self.response_schema)
        async def get_one(id: Any, db: AsyncSession = Depends(self.get_db)):
            item = await self.crud.get(db, id=id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return item

    def _register_create_route(self):
        @self.router.post(
            "/",
            response_model=self.response_schema,
            status_code=status.HTTP_201_CREATED,
        )
        async def create(
            data: self.create_schema,  # type: ignore
            db: AsyncSession = Depends(self.get_db),
        ):
            return await self.crud.create(db, obj_in=data)

    def _register_update_route(self):
        @self.router.patch("/{id}", response_model=self.response_schema)
        async def update(
            id: Any,
            data: self.update_schema,  # type: ignore
            db: AsyncSession = Depends(self.get_db),
        ):
            db_obj = await self.crud.get(db, id=id)
            if not db_obj:
                raise HTTPException(status_code=404, detail="Item not found")
            return await self.crud.update(db, db_model=db_obj, obj_in=data)

    def _register_delete_route(self):
        @self.router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete(id: Any, db: AsyncSession = Depends(self.get_db)):
            success = await self.crud.remove(db, id=id)
            if not success:
                raise HTTPException(status_code=404, detail="Item not found")
            return None

    async def get_router(self) -> APIRouter:
        return self.router
