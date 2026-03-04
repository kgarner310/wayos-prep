import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.industry import IndustryRiskProfile


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    # Use SQLite for tests to avoid needing Postgres
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite doesn't support ARRAY, so we need to handle this
    # We'll test the core logic rather than ORM models directly
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_profile():
    """Return a dict representing a sample industry profile."""
    return {
        "industry_name": "Roofing",
        "synonyms": ["roofer", "roofing contractor"],
        "top_workers_comp_claims": [
            "Falls from height",
            "Heat-related illness",
        ],
        "commercial_auto_claims": [
            "Material hauling accidents",
        ],
        "general_liability_exposures": [
            "Property damage from leaks",
            "Completed operations claims",
        ],
        "conversation_prompts": [
            "How do you manage fall protection?",
            "What's your subcontractor process?",
        ],
        "regional_risk_notes": "Hail belt exposure in TX, CO, OK.",
    }
