import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.config import settings
from app.database.base import Base
from app.database.connection import get_db
from app.main import app


test_engine = create_engine(settings.test_database_url)
TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_tables():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def moderator_headers(client):
    client.post("/auth/register", json={
        "username": "mod1",
        "email": "mod1@example.com",
        "password": "strongpass123",
        "invite_code": settings.moderator_invite_code,
    })
    response = client.post("/auth/login", json={"username": "mod1", "password": "strongpass123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_report(client):
    """Submits one report and returns the response body (contains the case code)."""
    response = client.post("/reports", json={
        "category": "SECURITY",
        "description": "The server room door is left open every night.",
        "evidence_url": "https://example.com/photo.jpg",
    })
    return response.json()
