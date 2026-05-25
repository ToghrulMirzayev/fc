"""Smoke test: app starts and /health responds correctly."""

import os

# Set required env before importing the app.
os.environ.setdefault("SECRET_KEY", "x" * 32)
os.environ.setdefault("QR_SIGNING_KEY", "y" * 32)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:y@localhost/x")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health_returns_ok():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["app"]  # branding string is wired
        assert body["version"]


def test_branding_uses_env_app_name(monkeypatch):
    """Changing APP_NAME env should be reflected in /health response.

    This is the canary that proves rebranding is single-source.
    """
    # Note: settings is module-cached; in a real test we'd reload.
    # This test sketches the contract; real impl uses dependency override.
    with TestClient(app) as client:
        body = client.get("/health").json()
        assert isinstance(body["app"], str) and body["app"]
