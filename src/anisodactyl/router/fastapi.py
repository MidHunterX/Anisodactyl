import math
from enum import Enum
from typing import Any, Generic, List, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing_extensions import Literal

from anisodactyl.crud._protocols import CRUDProtocol
from anisodactyl.query._protocols import QueryParserProtocol
from anisodactyl.query.anisodactyl import QueryParams  # Default Query Parser

from ._protocols import PaginatedResponse

SessionT = TypeVar("SessionT", contravariant=True)
ModelT = TypeVar("ModelT")
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)
ResponseSchemaT = TypeVar("ResponseSchemaT", bound=BaseModel)
JSONType = dict[str, Any]
RouteNames = Literal["get", "get_all", "create", "update", "delete"]


class RouterBase(
    Generic[ModelT, CreateSchemaT, UpdateSchemaT, ResponseSchemaT, SessionT]
):
    def __init__(
        self,
        *,
        # CRUD PARAMETERS
        # ===============
        model: Type[ModelT],
        crud: CRUDProtocol[ModelT, CreateSchemaT, UpdateSchemaT, SessionT],
        create_schema: Type[CreateSchemaT],
        update_schema: Type[UpdateSchemaT],
        response_schema: Type[ResponseSchemaT],
        get_db: Any,  # session dependency
        query_parser: Type[QueryParserProtocol] = QueryParams,
        # ROUTERBASE PARAMETERS
        # =====================
        exclude_routes: list[RouteNames] | None = None,
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

        self.exclude_routes = exclude_routes or []
        self._register_routes()

    def _register_routes(self):
        if "get_all" not in self.exclude_routes:
            self._register_getall_route()
        if "get" not in self.exclude_routes:
            self._register_getone_route()
        if "create" not in self.exclude_routes:
            self._register_create_route()
        if "update" not in self.exclude_routes:
            self._register_update_route()
        if "delete" not in self.exclude_routes:
            self._register_delete_route()

    def _register_getall_route(self):
        @self.router.get("/", response_model=PaginatedResponse[self.response_schema])
        async def get_all(
            db: SessionT = Depends(self.get_db),
            params: QueryParserProtocol = Depends(self.query_parser),
            limit: int = Query(default=10, le=100),
            page: int = Query(default=1, ge=1),
        ):
            items, total_count = await self.crud.get_multi(
                db=db,
                skip=(page - 1) * limit,
                limit=limit,
                filters=params.filters,
                sort=params.sort,
                fields=params.fields,
            )
            pages = math.ceil(total_count / limit) if total_count > 0 else 0
            return {
                "data": items,
                "pagination": {
                    "limit": limit,  # Items per page
                    "total": total_count,  # Total number of items
                    "page": page,  # Current page
                    "pages": pages,  # Total number of pages
                },
            }

        _ = get_all  # to suppress unused taggedHint

    def _register_getone_route(self):
        @self.router.get("/{id}", response_model=self.response_schema)
        async def get_one(id: Any, db: SessionT = Depends(self.get_db)) -> ModelT:
            item = await self.crud.get(db, id=id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            return item

        _ = get_one  # to suppress unused taggedHint

    def _register_create_route(self):
        @self.router.post(
            "/",
            response_model=self.response_schema,
            status_code=status.HTTP_201_CREATED,
        )
        async def create(
            data: self.create_schema,  # type: ignore
            db: SessionT = Depends(self.get_db),
        ) -> ModelT:
            return await self.crud.create(db, obj_in=data)

        _ = create  # to suppress unused taggedHint

    def _register_update_route(self):
        @self.router.patch("/{id}", response_model=self.response_schema)
        async def update(
            id: Any,
            data: self.update_schema,  # type: ignore
            db: SessionT = Depends(self.get_db),
        ) -> ModelT:
            db_obj = await self.crud.get(db, id=id)
            if not db_obj:
                raise HTTPException(status_code=404, detail="Item not found")
            return await self.crud.update(db, db_model=db_obj, obj_in=data)

        _ = update  # to suppress unused taggedHint

    def _register_delete_route(self):
        @self.router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete(id: Any, db: SessionT = Depends(self.get_db)) -> None:
            success = await self.crud.remove(db, id=id)
            if not success:
                raise HTTPException(status_code=404, detail="Item not found")
            return None

        _ = delete  # to suppress unused taggedHint

    async def get_router(self) -> APIRouter:
        return self.router
