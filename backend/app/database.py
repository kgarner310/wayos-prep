from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool, StaticPool

from app.config import settings

if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_max_overflow,
        pool_pre_ping=True,
        pool_recycle=1800,
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
