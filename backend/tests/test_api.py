import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_read_permits():
    response = client.get("/permits/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_ingest_permit():
    payload = {
        "permit_id": "TEST-001",
        "city": "San Francisco",
        "address": "123 Main St",
        "valuation": 500000,
        "status": "issued",
        "source_url": "https://example.com"
    }
    response = client.post("/permits/ingest", json=payload)
    assert response.status_code == 200
    assert response.json()["permit_id"] == "TEST-001"

def test_list_sources():
    response = client.get("/sources/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
