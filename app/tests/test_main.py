import pytest
from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient

from app.main import Settings, verify_api_key


def test_valid_api_key_allows_access():
    cfg = Settings(API_KEY="supersecret")
    # Should not raise
    verify_api_key(cfg, "supersecret")


def test_uses_x_api_key_header_alias():
    # Use default API key from Settings (dev-secret) to avoid dependency patching
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_api_key)])
    def protected():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/protected", headers={"X-API-KEY": "dev-secret"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"ok": True}


def test_accepts_special_characters_in_api_key():
    special_key = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~🙂"
    cfg = Settings(API_KEY=special_key)
    # Should not raise
    verify_api_key(cfg, special_key)


def test_missing_api_key_header_denied_401():
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_api_key)])
    def protected():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/protected")  # no header
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json()["detail"] == "Invalid or missing API key"


def test_incorrect_api_key_denied_401():
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_api_key)])
    def protected():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/protected", headers={"X-API-KEY": "wrong"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json()["detail"] == "Invalid or missing API key"


@pytest.mark.parametrize("bad_value", ["", "   "])
def test_blank_api_key_header_denied_401(bad_value: str):
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_api_key)])
    def protected():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/protected", headers={"X-API-KEY": bad_value})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    assert resp.json()["detail"] == "Invalid or missing API key"