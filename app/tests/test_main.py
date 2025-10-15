import pytest
from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient

from app.main import Settings, get_settings, verify_api_key


class TestVerifyApiKey:
    def test_verify_api_key_accepts_matching_key(self):
        cfg = Settings()
        # Should not raise
        assert verify_api_key(cfg=cfg, x_api_key=cfg.API_KEY) is None

    def test_verify_api_key_uses_overridden_settings_value(self):
        custom_key = "custom-secret-key-123"
        cfg = Settings(API_KEY=custom_key)
        # Accepts the custom key
        assert verify_api_key(cfg=cfg, x_api_key=custom_key) is None
        # Rejects a different key
        with pytest.raises(Exception) as excinfo:
            verify_api_key(cfg=cfg, x_api_key="some-other-key")
        assert getattr(excinfo.value, "status_code", None) == status.HTTP_401_UNAUTHORIZED
        assert getattr(excinfo.value, "detail", None) == "Invalid or missing API key"

    def test_verify_api_key_reads_case_insensitive_header_alias(self):
        app = FastAPI()

        @app.get("/protected", dependencies=[Depends(verify_api_key)])
        def protected():
            return {"ok": True}

        client = TestClient(app)
        api_key = get_settings().API_KEY
        # Use lowercase header name to verify case-insensitivity with the alias
        resp = client.get("/protected", headers={"x-api-key": api_key})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_verify_api_key_missing_header_raises_401(self):
        cfg = Settings()
        with pytest.raises(Exception) as excinfo:
            verify_api_key(cfg=cfg)
        assert getattr(excinfo.value, "status_code", None) == status.HTTP_401_UNAUTHORIZED
        assert getattr(excinfo.value, "detail", None) == "Invalid or missing API key"

    def test_verify_api_key_incorrect_value_raises_401(self):
        cfg = Settings()
        with pytest.raises(Exception) as excinfo:
            verify_api_key(cfg=cfg, x_api_key="incorrect-key")
        assert getattr(excinfo.value, "status_code", None) == status.HTTP_401_UNAUTHORIZED
        assert getattr(excinfo.value, "detail", None) == "Invalid or missing API key"

    def test_verify_api_key_blank_or_whitespace_value_raises_401(self):
        cfg = Settings()
        # Empty string
        with pytest.raises(Exception) as excinfo_empty:
            verify_api_key(cfg=cfg, x_api_key="")
        assert getattr(excinfo_empty.value, "status_code", None) == status.HTTP_401_UNAUTHORIZED
        assert getattr(excinfo_empty.value, "detail", None) == "Invalid or missing API key"

        # Whitespace-only string
        with pytest.raises(Exception) as excinfo_ws:
            verify_api_key(cfg=cfg, x_api_key="   ")
        assert getattr(excinfo_ws.value, "status_code", None) == status.HTTP_401_UNAUTHORIZED
        assert getattr(excinfo_ws.value, "detail", None) == "Invalid or missing API key"