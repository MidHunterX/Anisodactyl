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
    """SQLAlchemy model for testing."""
    __tablename__ = "test_model"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)


class CreateSchema(BaseModel):
    """Pydantic schema for testing."""
    name: str
    description: Optional[str] = None


class UpdateSchema(BaseModel):
    """Pydantic schema for testing."""
    name: Optional[str] = None
    description: Optional[str] = None


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
