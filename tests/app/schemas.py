from typing import Optional

from pydantic import BaseModel


class ParentCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None


class ChildCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None


class CreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    parent: Optional[ParentCreateSchema] = None
    child: Optional[ChildCreateSchema] = None
    child2: Optional[ChildCreateSchema] = None


class UpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ResponseSchema(BaseModel):
    id: int  # id exposed for testing purposes only
    name: str
    description: Optional[str]
