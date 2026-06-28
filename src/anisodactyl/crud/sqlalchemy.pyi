from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from ._protocols import CRUDProtocol, FilterDict

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# CRUDBase is the protocol instantiated with AsyncSession
class CRUDBase(
    CRUDProtocol[ModelType, CreateSchemaType, UpdateSchemaType, AsyncSession]
): ...

__all__ = ["CRUDBase", "FilterDict"]
