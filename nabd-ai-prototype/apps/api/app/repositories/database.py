"""Engine, session and dialect-portable column types.

PostgreSQL 16 is the required database. SQLite is permitted only for isolated unit tests,
so every column type used here declares an explicit SQLite variant rather than relying on
implicit coercion.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import JSON, Engine, MetaData, create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

#: JSONB on PostgreSQL, JSON on SQLite.
JsonPayload = JSONB().with_variant(JSON(), "sqlite")  # type: ignore[no-untyped-call]


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _configure_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def build_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    url = database_url or settings.database_url
    connect_args: dict[str, Any] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine = create_engine(url, future=True, connect_args=connect_args)
        _configure_sqlite(engine)
        return engine
    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=2,
        connect_args={"application_name": "nabd-ai-prototype"},
    )


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), autoflush=False, expire_on_commit=False, future=True
        )
    return _session_factory


def reset_engine(engine: Engine | None = None) -> None:
    """Rebind the module-level engine. Used by tests and by the seeding scripts."""
    global _engine, _session_factory
    if _engine is not None and engine is not _engine:
        _engine.dispose()
    _engine = engine
    _session_factory = None


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Transactional scope. A failure rolls back the state transition and its audit event."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency."""
    with session_scope() as session:
        yield session
