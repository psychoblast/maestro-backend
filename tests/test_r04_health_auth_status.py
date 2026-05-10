"""
R-04 follow-up — /api/admin/health/deep reports security posture.

New fields required:
  auth_enabled:                  bool
  auth_mode:                     "enforced" | "dev-permissive"
  anthropic_available:           bool
  stripe_signed_webhooks_required: bool
  cors_origins:                  str

Run with:  python3 -m pytest tests/test_r04_health_auth_status.py -v
"""

import importlib
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    import admin_service
    importlib.reload(admin_service)
    # Create the tables that admin_service reads
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY, data TEXT DEFAULT '{}'
        );
    """)
    conn.commit()
    conn.close()
    yield db


def _client(monkeypatch, **env):
    for k, v in env.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)
    import admin_service
    importlib.reload(admin_service)
    app = FastAPI()
    app.include_router(admin_service.router)
    return TestClient(app)


def _deep(client) -> dict:
    resp = client.get("/api/admin/health/deep")
    assert resp.status_code == 200
    return resp.json()


# ── New fields are present ─────────────────────────────────────────────────────

def test_all_security_fields_present(monkeypatch):
    client = _client(monkeypatch)
    data = _deep(client)
    for field in ("auth_enabled", "auth_mode", "anthropic_available",
                  "stripe_signed_webhooks_required", "cors_origins"):
        assert field in data, f"Missing field: {field}"


# ── auth_enabled / auth_mode ──────────────────────────────────────────────────

def test_auth_enabled_when_key_set(monkeypatch):
    client = _client(monkeypatch, PLMKR_API_KEY="secret")
    data = _deep(client)
    assert data["auth_enabled"] is True
    assert data["auth_mode"] == "enforced"


def test_auth_disabled_when_key_absent(monkeypatch):
    client = _client(monkeypatch, PLMKR_API_KEY=None)
    data = _deep(client)
    assert data["auth_enabled"] is False
    assert data["auth_mode"] == "dev-permissive"


# ── anthropic_available ───────────────────────────────────────────────────────

def test_anthropic_available_reflects_key(monkeypatch):
    client_yes = _client(monkeypatch, ANTHROPIC_API_KEY="sk-test")
    assert _deep(client_yes)["anthropic_available"] is True

    client_no = _client(monkeypatch, ANTHROPIC_API_KEY=None)
    assert _deep(client_no)["anthropic_available"] is False


# ── stripe_signed_webhooks_required ──────────────────────────────────────────

def test_stripe_signed_when_secret_set(monkeypatch):
    client = _client(monkeypatch,
                     STRIPE_WEBHOOK_SECRET="whsec_test",
                     STRIPE_DEV_ALLOW_UNSIGNED=None)
    assert _deep(client)["stripe_signed_webhooks_required"] is True


def test_stripe_not_signed_only_when_secret_absent_and_dev_flag_set(monkeypatch):
    client = _client(monkeypatch,
                     STRIPE_WEBHOOK_SECRET=None,
                     STRIPE_DEV_ALLOW_UNSIGNED="true")
    assert _deep(client)["stripe_signed_webhooks_required"] is False


# ── cors_origins ──────────────────────────────────────────────────────────────

def test_cors_origins_reflects_env(monkeypatch):
    client = _client(monkeypatch, ALLOWED_ORIGINS="https://plmkr.vercel.app")
    data = _deep(client)
    assert data["cors_origins"] == "https://plmkr.vercel.app"


def test_cors_origins_defaults_to_wildcard(monkeypatch):
    client = _client(monkeypatch, ALLOWED_ORIGINS=None)
    data = _deep(client)
    assert data["cors_origins"] == "*"
