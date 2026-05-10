"""
R-12 — /send-test-email must not exist.

The endpoint was an unauthenticated debug route that exposed SMTP credentials
and could be triggered by anyone with network access.  The fix is hard deletion
of the route from main.py.

Run with:  python3 -m pytest tests/test_r12_send_test_email_removed.py -v
"""

import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-test")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test")
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        yield TestClient(m.app)


def test_send_test_email_returns_404(client):
    """Route must not exist — returns 404, not 200/500."""
    resp = client.get("/send-test-email")
    assert resp.status_code == 404, (
        f"Expected 404 (route deleted), got {resp.status_code}. "
        "The /send-test-email route still exists in main.py — remove it."
    )


def test_route_not_in_app_routes(client):
    """Belt-and-suspenders: /send-test-email must not appear in app.routes."""
    import main as m
    paths = [getattr(r, "path", "") for r in m.app.routes]
    assert "/send-test-email" not in paths, (
        "/send-test-email is still registered as an app route"
    )
