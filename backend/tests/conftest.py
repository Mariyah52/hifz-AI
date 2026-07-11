import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
import app.models  # noqa: F401 — ensures every model is registered on Base.metadata

TEST_ENGINE = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture()
def db_session():
    """A fresh in-memory database, tables created and dropped per test — no shared state between tests."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture()
def client(db_session):
    """
    A TestClient wired to the same in-memory DB as `db_session`, via a
    dependency override — imports app.main lazily (inside the fixture)
    so importing this conftest doesn't have side effects for tests that
    only need `db_session` and never touch the HTTP layer.
    """
    from app.main import app
    from app.rate_limit import limiter

    # slowapi's Limiter keeps its counters in a module-level singleton, so
    # without resetting it here, rate limits tripped by an earlier test
    # would leak into this one (same fake client IP every time).
    limiter.reset()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Small factory helpers, shared across test modules -----------------


def make_organization(db, name="Test Org", slug="test-org", **overrides):
    from app.models.organization import Organization

    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        return existing

    org = Organization(name=name, slug=slug, plan="free", max_students=30, max_teachers=5, **overrides)
    db.add(org)
    db.flush()
    return org


def make_user(db, email="student@example.com", name="Test Student", role="student", password_hash="x", organization=None):
    from app.models.user import User

    org = organization or make_organization(db)
    user = User(email=email, name=name, role=role, hashed_password=password_hash, organization_id=org.id)
    db.add(user)
    db.flush()
    return user


def make_student(db, **user_kwargs):
    from app.models.user import StudentProfile

    user = make_user(db, **user_kwargs)
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    db.flush()
    return profile
