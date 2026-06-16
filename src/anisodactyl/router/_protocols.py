from typing import Generic, TypeVar, Sequence

from pydantic import BaseModel

T = TypeVar("T")


class PaginationInfo(BaseModel):
    total: int
    page: int
    limit: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: Sequence[T]
    pagination: PaginationInfo
