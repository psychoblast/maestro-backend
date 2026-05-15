"""
A2 — Admin diagnostics endpoint.

Tests:
- 401 without API key
- 200 with valid API key
- env_snapshot never leaks actual values (sentinel check)
- service_status correct shape
- recent_errors captures ERROR log entries
"""

import importlib
import json
import logging
from unittest.mock import MagicMock, patch

import pytest


# ── helpers ────────────────────────────────────────────────────────────────────

_SENTINEL_KEY = "sk-ant-test-SENTINEL-VALUE"
_PLMKR_KEY    = "test-plmkr-key"


def _build_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    monkeypatch.setenv("PLMKR_API_KEY",      _PLMKR_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY",  _SENTINEL_KEY)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)

    from fastapi.testclient import TestClient
    return TestClient(m.app, raise_server_exceptions=False)


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_diagnostics_401_without_key(monkeypatch, tmp_path):
    """GET /api/admin/diagnostics must return 401 when API key is missing."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics")
    assert resp.status_code == 401


def test_diagnostics_200_with_key(monkeypatch, tmp_path):
    """GET /api/admin/diagnostics must return 200 with a valid X-API-Key."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics", headers={"X-API-Key": _PLMKR_KEY})
    assert resp.status_code == 200
    body = resp.json()
    assert "env_snapshot"   in body
    assert "service_status" in body
    assert "runtime"        in body
    assert "volume"         in body
    assert "scheduler"      in body
    assert "recent_errors"  in body
    assert "timestamp"      in body


def test_env_snapshot_never_leaks_values(monkeypatch, tmp_path):
    """env_snapshot must contain only SET/MISSING — never the actual value."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics", headers={"X-API-Key": _PLMKR_KEY})
    assert resp.status_code == 200
    body_text = resp.text
    # The sentinel must NOT appear anywhere in the response body
    assert _SENTINEL_KEY not in body_text, (
        f"Sentinel value leaked into response body:\n{body_text}"
    )
    # Confirmed set key should appear as "SET"
    snapshot = resp.json()["env_snapshot"]
    assert snapshot.get("ANTHROPIC_API_KEY") == "SET"


def test_env_snapshot_missing_for_unset(monkeypatch, tmp_path):
    """Unset env vars must show as MISSING in env_snapshot."""
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics", headers={"X-API-Key": _PLMKR_KEY})
    snapshot = resp.json()["env_snapshot"]
    assert snapshot.get("SENTRY_DSN") == "MISSING"


def test_service_status_correct_shape(monkeypatch, tmp_path):
    """service_status must contain known service keys with bool values."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics", headers={"X-API-Key": _PLMKR_KEY})
    svc = resp.json()["service_status"]
    for key in ("anthropic", "gmail", "stripe", "twilio", "buffer", "elevenlabs", "d_id", "cloudinary"):
        assert key in svc, f"Missing service: {key}"
        assert isinstance(svc[key], bool)
    # anthropic key is set to sentinel — must be True
    assert svc["anthropic"] is True


def test_recent_errors_captures_error_log(monkeypatch, tmp_path):
    """An ERROR log emitted after the app loads must appear in recent_errors."""
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    monkeypatch.setenv("PLMKR_API_KEY",      _PLMKR_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY",  _SENTINEL_KEY)

    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)

    # Emit an ERROR into the root logger so the ring buffer captures it
    import logging_config
    importlib.reload(logging_config)
    logging_config.setup_logging()
    logging.getLogger("test.diag").error("ring-buffer-test-error-XYZ")

    from fastapi.testclient import TestClient
    client = TestClient(m.app, raise_server_exceptions=False)
    resp = client.get("/api/admin/diagnostics", headers={"X-API-Key": _PLMKR_KEY})
    assert resp.status_code == 200
    errors = resp.json()["recent_errors"]
    msgs = [e.get("msg", "") for e in errors]
    assert any("ring-buffer-test-error-XYZ" in msg for msg in msgs), (
        f"Expected ring-buffer error in recent_errors. Got: {errors}"
    )
