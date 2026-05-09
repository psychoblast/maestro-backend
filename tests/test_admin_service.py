"""
Unit tests for admin_service.py — all DB interactions mocked.

Run with:  python3 -m pytest tests/test_admin_service.py -v
"""

import importlib
import sqlite3
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    import admin_service
    importlib.reload(admin_service)
    # Initialise the tables that admin_service reads
    conn = sqlite3.connect(str(db))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pitches (
            id TEXT PRIMARY KEY, artist_id TEXT, status TEXT,
            created_at TEXT DEFAULT '2026-01-01T00:00:00'
        );
        CREATE TABLE IF NOT EXISTS pr_outreach (
            id TEXT PRIMARY KEY, artist_id TEXT, status TEXT,
            created_at TEXT DEFAULT '2026-01-01T00:00:00'
        );
        CREATE TABLE IF NOT EXISTS booking_inquiries (
            id TEXT PRIMARY KEY, artist_id TEXT, status TEXT,
            created_at TEXT DEFAULT '2026-01-01T00:00:00'
        );
        CREATE TABLE IF NOT EXISTS social_posts (
            id TEXT PRIMARY KEY, artist_id TEXT, status TEXT,
            created_at TEXT DEFAULT '2026-01-01T00:00:00'
        );
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id TEXT PRIMARY KEY, artist_id TEXT, generated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY, data TEXT DEFAULT '{}'
        );
    """)
    conn.commit()
    conn.close()
    yield db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import admin_service
    importlib.reload(admin_service)
    app = FastAPI()
    app.include_router(admin_service.router)
    return TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _insert_pitch(db, artist_id, status):
    import uuid
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO pitches (id, artist_id, status) VALUES (?,?,?)",
        (str(uuid.uuid4()), artist_id, status),
    )
    conn.commit()
    conn.close()


def _insert_social_post(db, artist_id, status):
    import uuid
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO social_posts (id, artist_id, status) VALUES (?,?,?)",
        (str(uuid.uuid4()), artist_id, status),
    )
    conn.commit()
    conn.close()


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_stats_returns_zero_for_new_artist(client):
    resp = client.get("/api/admin/stats?artist_id=artist-new")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pitches_sent"] == 0
    assert data["reply_rate"]   == 0.0
    assert data["artist_id"]    == "artist-new"


def test_stats_counts_sent_pitches(client, temp_db):
    _insert_pitch(temp_db, "artist-a", "sent")
    _insert_pitch(temp_db, "artist-a", "sent")
    _insert_pitch(temp_db, "artist-a", "replied")
    resp = client.get("/api/admin/stats?artist_id=artist-a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pitches_sent"]    == 3   # sent + replied both count as non-draft
    assert data["pitches_replied"] == 1
    assert data["reply_rate"]      == round(1 / 3, 2)


def test_stats_counts_social_posts_published(client, temp_db):
    _insert_social_post(temp_db, "artist-b", "posted")
    _insert_social_post(temp_db, "artist-b", "draft")
    resp = client.get("/api/admin/stats?artist_id=artist-b")
    assert resp.status_code == 200
    assert resp.json()["social_posts_published"] == 1


def test_stats_requires_artist_id(client):
    resp = client.get("/api/admin/stats")
    assert resp.status_code == 422  # FastAPI validation: missing required query param


def test_deep_health_returns_expected_keys(client):
    with patch("admin_service._check_scheduler_running", return_value=False):
        resp = client.get("/api/admin/health/deep")
    assert resp.status_code == 200
    data = resp.json()
    assert "db_connected"                    in data
    assert "scheduler_running"               in data
    assert "gmail_token_valid_for_artists"   in data
    assert "buffer_token_valid_for_artists"  in data
    assert "disk_usage_pct"                  in data
    assert data["db_connected"] is True


def test_deep_health_counts_gmail_tokens(client, temp_db):
    import json
    conn = sqlite3.connect(str(temp_db))
    conn.execute(
        "INSERT INTO artists (artist_id, data) VALUES (?,?)",
        ("a1", json.dumps({"gmail_tokens": {"access_token": "tok123"}})),
    )
    conn.execute(
        "INSERT INTO artists (artist_id, data) VALUES (?,?)",
        ("a2", json.dumps({"gmail_tokens": {}})),
    )
    conn.commit()
    conn.close()
    with patch("admin_service._check_scheduler_running", return_value=False):
        resp = client.get("/api/admin/health/deep")
    assert resp.json()["gmail_token_valid_for_artists"] == 1
