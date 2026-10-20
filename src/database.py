from __future__ import annotations

import asyncio

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.database_url, echo=False)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    """Enable FK enforcement on every new SQLite connection.

    SQLite ignores ON DELETE SET NULL (and other FK actions) unless
    PRAGMA foreign_keys = ON is set per connection.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Bring the schema up to date by running Alembic migrations to head.

    Alembic's command API is synchronous; for SQLite single-file this is fine
    to call at startup via asyncio.to_thread.
    """
    from alembic import command
    from alembic.config import Config

    def _upgrade() -> None:
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")

    await asyncio.to_thread(_upgrade)


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
