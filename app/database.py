"""Async SQLAlchemy engine and session for SQLite with WAL mode."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import event, text
from app.config import settings

engine = create_async_engine(
    settings.database_url_resolved,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Set SQLite pragmas for performance on every new connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA cache_size=-20000;")  # ~20MB
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


# Register the pragma setter on the sync engine events
event.listen(engine.sync_engine, "connect", _set_sqlite_pragmas)


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
