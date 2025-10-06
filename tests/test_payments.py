import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, Base, get_db, Settings, get_settings


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("ENV", "test")
    # Use in-memory SQLite for tests
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")


@pytest.fixture()
def client(monkeypatch):
    # Create new engine per test session to avoid cross-test bleed
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Clear cached settings to pick up env overrides
    get_settings.cache_clear()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def auth_headers():
    return {"X-API-KEY": os.getenv("API_KEY", "test-key")}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


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


def test_create_payment_missing_api_key(client):
    payload = {"order_id": "ORD123", "amount": 10.5, "currency": "USD"}
    r = client.post("/payments", json=payload)
    assert r.status_code == 401


def test_create_payment_invalid_amount(client):
    payload = {"order_id": "ORD123", "amount": -1, "currency": "USD"}
    r = client.post("/payments", json=payload, headers=auth_headers())
    assert r.status_code == 422  # validation error from Pydantic
