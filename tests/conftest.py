from typing import Optional

import pytest_asyncio
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# █▀▄▀█ █▀█ █▀▄ █▀▀ █░░ █▀
# █░▀░█ █▄█ █▄▀ ██▄ █▄▄ ▄█


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


# ▀█▀ █▀▀ █▀ ▀█▀   █▀ █▀▀ ▀█▀ █░█ █▀█
# ░█░ ██▄ ▄█ ░█░   ▄█ ██▄ ░█░ █▄█ █▀▀

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def override_get_db(db_session):
    async def _get_db():
        yield db_session

    return _get_db
