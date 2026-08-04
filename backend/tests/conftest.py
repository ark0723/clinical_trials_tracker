import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.db import Base
from app.services.geo import StaticZipGeocoder, set_zip_geocoder
from app.services.trial_match_loader import clear_candidate_cache
from app.services.user_profile_service import clear_profile_cache


@pytest.fixture(autouse=True)
def _clear_match_candidate_cache():
    clear_candidate_cache()
    clear_profile_cache()
    set_zip_geocoder(StaticZipGeocoder({}))
    yield
    clear_candidate_cache()
    clear_profile_cache()
    set_zip_geocoder(None)


@pytest.fixture()
def db_session() -> Session:
    """Fast, isolated SQLite in-memory DB for each test (see plan's design decisions)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
