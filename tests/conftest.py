"""Test configuration and fixtures."""

import os
import pytest

# Override database URL before any imports
os.environ.setdefault("DATABASE_URL", "postgresql://wayos:wayos_dev_password@localhost:5432/wayos_prep_test")


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    from sqlalchemy import create_engine, text as sa_text
    TEST_DATABASE_URL = os.environ.get("DATABASE_URL")
    try:
        eng = create_engine(TEST_DATABASE_URL)
        with eng.connect() as conn:
            conn.execute(sa_text("SELECT 1"))
        return eng
    except Exception:
        pytest.skip("Test database not available")


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables."""
    from sqlalchemy import text as sa_text
    from app.db.session import Base
    import app.models.models  # noqa: F401
    with engine.connect() as conn:
        conn.execute(sa_text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(sa_text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables):
    """Create a test database session."""
    from sqlalchemy.orm import sessionmaker
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create a test FastAPI client."""
    from fastapi.testclient import TestClient
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
