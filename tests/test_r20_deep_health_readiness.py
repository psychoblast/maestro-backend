"""
R-20 — Railway healthcheck is liveness-only; DB and scheduler failures undetected.

Fix: /api/admin/health/deep returns 503 when db_connected=False so Railway
restarts the container on DB failure instead of serving a degraded process.

Red-green verified:
  - On main (before fix): DB-down request returns 200  → test_db_down_returns_503 FAILS
  - On this branch:       DB-down request returns 503  → test_db_down_returns_503 PASSES
"""

import importlib
import os
import sqlite3
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    import admin_service
    importlib.reload(admin_service)
    conn = sqlite3.connect(str(db))
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS artists (artist_id TEXT PRIMARY KEY, data TEXT DEFAULT '{}');"
    )
    conn.commit()
    conn.close()
    yield db


@pytest.fixture()
def client():
    import admin_service
    importlib.reload(admin_service)
    app = FastAPI()
    app.include_router(admin_service.router)
    return TestClient(app)


def test_db_down_returns_503(client):
    """Core R-20 fix: DB failure must produce 503, not 200."""
    with patch("admin_service._check_db_connected", return_value=False), \
         patch("admin_service._check_scheduler_running", return_value=False):
        resp = client.get("/api/admin/health/deep")
    assert resp.status_code == 503
    assert resp.json()["db_connected"] is False


def test_db_up_returns_200(client):
    """Healthy DB must still return 200 — no false positives."""
    with patch("admin_service._check_scheduler_running", return_value=False):
        resp = client.get("/api/admin/health/deep")
    assert resp.status_code == 200
    assert resp.json()["db_connected"] is True


def test_db_down_body_still_contains_all_fields(client):
    """503 response must still carry full diagnostic JSON body."""
    with patch("admin_service._check_db_connected", return_value=False), \
         patch("admin_service._check_scheduler_running", return_value=False):
        resp = client.get("/api/admin/health/deep")
    data = resp.json()
    assert "db_connected"                    in data
    assert "scheduler_running"               in data
    assert "gmail_token_valid_for_artists"   in data
    assert "buffer_token_valid_for_artists"  in data
    assert "disk_usage_pct"                  in data
    assert "timestamp"                       in data
