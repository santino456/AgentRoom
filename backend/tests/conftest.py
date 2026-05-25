import sys
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from database import Base, get_db
from fastapi.testclient import TestClient
from main import app
from rate_limiter import limiter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# In-memory SQLite for tests (StaticPool ensures all connections share the same DB)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Monkeypatch main module's engine reference so lifespan uses test DB
import main as main_module  # noqa: E402

main_module._db_engine = engine


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    # Create tables fresh for each test
    Base.metadata.create_all(bind=engine)
    limiter._requests.clear()
    with TestClient(app) as c:
        yield c
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
    Base.metadata.drop_all(bind=engine)
