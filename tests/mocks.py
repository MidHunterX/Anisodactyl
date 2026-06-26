from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Model(Base):
    __tablename__ = "test_model"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)


class CreateSchema(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ResponseSchema(BaseModel):
    id: int  # id exposed for testing purposes only
    name: str
    description: Optional[str]


# ===============================[ API AREA ]=============================== #

from fastapi import Request


@staticmethod
def create_mock_request(query_string: str) -> Request:
    """Helper to create a FastAPI request with specific query params."""
    scope = {"type": "http", "query_string": query_string.encode()}
    return Request(scope)
