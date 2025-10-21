import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db, _create_engine
from app.models import Base
from app.core.config import Settings, get_settings

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("ENV", "test")
    # Use in-memory SQLite for tests
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

@pytest.fixture()
def client():
    # Clear cached settings to pick up env overrides from set_env fixture
    get_settings.cache_clear()
    
    # Create test engine with in-memory SQLite
    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
def auth_headers():
    # Get API key from centralized config, which will pick up the test environment override
    settings = get_settings()
    return {"X-API-KEY": settings.API_KEY}

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
# def test_create_payment_happy_path(client):
#     payload = {"order_id": "ORD123", "amount": 10.5, "currency": "USD"}
#     r = client.post("/payments", json=payload, headers=auth_headers())
#     assert r.status_code == 201
#     body = r.json()
#     assert body["order_id"] == "ORD123"
#     assert body["amount"] == 10.5
#     assert body["currency"] == "USD"
#     assert "id" in body
#     assert "created_at" in body

def test_create_payment_missing_api_key(client):
    payload = {"order_id": "ORD123", "amount": 10.5, "currency": "USD"}
    r = client.post("/payments", json=payload)
    assert r.status_code == 401

def test_create_payment_invalid_amount(client):
    payload = {"order_id": "ORD123", "amount": -1, "currency": "USD"}
    r = client.post("/payments", json=payload, headers=auth_headers())
    assert r.status_code == 422  # validation error from Pydantic


def test_create_payment_happy_path(client):
    payload = {"order_id": "ORD123", "amount": 10.5, "currency": "USD"}
    r = client.post("/payments", json=payload, headers=auth_headers())
    assert r.status_code == 201
    body = r.json()
    assert body["order_id"] == "ORD123"
    assert body["amount"] == 10.5
    assert body["currency"] == "USD"
    assert "id" in body
    assert "created_at" in body


def test_amount_is_rounded_to_two_decimals_on_create(client):
    payload = {"order_id": "ORD-ROUND", "amount": 10.556, "currency": "USD"}
    r = client.post("/payments", json=payload, headers=auth_headers())
    assert r.status_code == 201
    body = r.json()
    assert body["amount"] == pytest.approx(10.56, abs=1e-9)


def test_currency_defaults_to_usd_when_omitted(client):
    payload = {"order_id": "ORD-DEFAULT", "amount": 12.34}
    r = client.post("/payments", json=payload, headers=auth_headers())
    assert r.status_code == 201
    body = r.json()
    assert body["currency"] == "USD"


def test_non_usd_currency_rejected(client):
    payload = {"order_id": "ORD-EUR", "amount": 5.0, "currency": "EUR"}
    r = client.post("/payments", json=payload, headers=auth_headers())
    assert r.status_code == 422


def test_ready_returns_503_when_db_exec_fails():
    class FailingSession:
        def execute(self, *args, **kwargs):
            raise RuntimeError("db down")

    def failing_get_db():
        yield FailingSession()

    # override dependency to simulate DB failure
    app.dependency_overrides[get_db] = failing_get_db
    try:
        with TestClient(app) as c:
            r = c.get("/ready")
            assert r.status_code == 503
            assert r.json()["detail"] == "Database not ready"
    finally:
        app.dependency_overrides.clear()
