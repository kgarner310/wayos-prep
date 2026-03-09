"""Test configuration and fixtures."""

import os
import pytest
from uuid import uuid4

# Override database URL before any imports
os.environ.setdefault("DATABASE_URL", "postgresql://wayos:wayos@localhost:5432/wayos_prep_test")


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


@pytest.fixture(autouse=True)
def _bypass_auth():
    """Provide a mock authenticated user for all tests.

    Tests that specifically test auth behavior (test_auth.py) can
    override this by clearing dependency_overrides in their fixtures.
    """
    from app.api.deps import get_current_user, CurrentUser
    from app.main import app

    mock_user = CurrentUser(
        user_id=uuid4(),
        agency_id=uuid4(),
        role="admin",
        email="test@wayos.ai",
        full_name="Test User",
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield mock_user
    app.dependency_overrides.pop(get_current_user, None)
