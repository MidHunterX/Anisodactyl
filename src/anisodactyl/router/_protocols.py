from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel

Items = TypeVar("Items")


class PaginationInfo(BaseModel):
    limit: int  # Items per page
    total: int  # Total number of items
    page: int  # Current page
    pages: int  # Total number of pages


class PaginatedResponse(BaseModel, Generic[Items]):
    data: Sequence[Items]
    pagination: PaginationInfo
