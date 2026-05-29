"""Runtime SQLAlchemy async session wiring.

This module intentionally exposes factories so tests and future workers can create
isolated engines without mutating the process-global application engine.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def make_async_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Create an async SQLAlchemy engine for the provided database URL."""
    if ":memory:" in database_url:
        return create_async_engine(
            database_url,
            echo=echo,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(database_url, echo=echo, pool_pre_ping=True)


def make_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a typed async session factory bound to an engine."""
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async_engine = make_async_engine(get_settings().database_url)
AsyncSessionLocal = make_async_sessionmaker(async_engine)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped async database session."""
    async with AsyncSessionLocal() as session:
        yield session
