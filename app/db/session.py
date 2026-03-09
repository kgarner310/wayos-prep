import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL
        connect_args = {"connect_timeout": 10}

        # Supabase and other managed Postgres require SSL for external connections
        if "supabase" in db_url or "neon" in db_url:
            connect_args["sslmode"] = "require"

        _engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        logger.info("Database engine created (pool_pre_ping=True, connect_timeout=10)")
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _session_factory


def SessionLocal():
    """Create a new database session."""
    return _get_session_factory()()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_engine():
    """Reset engine and session factory (for testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None
