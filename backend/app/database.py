"""
BizPilot AI - Database Setup
Provides SQLAlchemy engine, session factory, declarative base,
FastAPI dependency, and utility functions.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

try:
    from app.config import get_settings
except ImportError:
    from backend.app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Engine creation
# ---------------------------------------------------------------------------

def _build_connect_args() -> dict:
    """Return driver-specific connect_args."""
    if settings.is_sqlite:
        # Allow SQLite to be used across threads (needed for FastAPI)
        return {"check_same_thread": False}
    return {}


def _build_engine() -> Engine:
    """Create and configure the SQLAlchemy engine."""
    connect_args = _build_connect_args()

    engine = create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,          # validate connections before use
        pool_recycle=3600,           # recycle connections every hour
        echo=settings.debug,         # echo SQL when DEBUG=true
    )

    # Enable WAL mode for SQLite to improve concurrent read performance
    if settings.is_sqlite:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):  # noqa: ANN001
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine: Engine = _build_engine()

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """
    Shared declarative base for all ORM models.

    All model classes should inherit from this base so that
    ``init_db()`` can discover and create their tables.
    """
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and ensures
    it is closed after the request completes.

    Usage::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context-manager version of get_db() for use outside of FastAPI
    (e.g., scripts, background tasks, tests).

    Usage::

        with get_db_context() as db:
            users = db.query(User).all()
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Table management
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create all tables defined on ``Base``.

    Import all model modules before calling this so that SQLAlchemy
    can discover the table definitions.

    Example (in main.py)::

        import app.models  # noqa: F401 – registers all models
        from app.database import init_db
        init_db()
    """
    # Import models so their tables are registered on Base.metadata
    try:
        import app.models  # noqa: F401
    except ImportError:
        try:
            import backend.app.models  # noqa: F401
        except ImportError:
            pass  # Models package not yet available (e.g. during early bootstrap)

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop ALL tables. Use with caution – intended for tests only.
    """
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

async def health_check() -> dict:
    """
    Async-compatible health check that verifies the database is reachable.

    Returns a dict with ``status``, ``latency_ms``, and ``database`` keys.
    """
    start = time.monotonic()
    status = "healthy"
    error_message: str | None = None

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        status = "unhealthy"
        error_message = str(exc)

    latency_ms = round((time.monotonic() - start) * 1000, 2)

    result: dict = {
        "status": status,
        "latency_ms": latency_ms,
        "database": settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
    }
    if error_message:
        result["error"] = error_message

    return result
