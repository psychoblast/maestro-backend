"""
Unit 4 — GET /api/admin/diagnostics/scheduler tests.

Covers:
- 401 without API key
- 200 with valid key, correct response shape on empty DB
- next_pending lists pending actions sorted by scheduled_for ASC (max 10)
- last_completed lists done/failed actions sorted by executed_at DESC (max 20)
- counts_24h groups by status for actions created within last 24 hours
"""

import importlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

_PLMKR_KEY = "sched-diag-test-key"


def _build_client(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH",           db_path)
    monkeypatch.setenv("DATABASE_URL",      "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",   str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",       str(tmp_path / "artists"))
    monkeypatch.setenv("PLMKR_API_KEY",     _PLMKR_KEY)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    # Reload service modules so their _DB_PATH picks up the new DB_PATH env var
    import admin_service, release_service
    importlib.reload(admin_service)
    importlib.reload(release_service)

    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)

    from fastapi.testclient import TestClient
    return TestClient(m.app, raise_server_exceptions=False), db_path


def _insert_action(db_path, *, action_id=None, release_id="rel-001", action_type="pitch_curators",
                   scheduled_for=None, status="pending", executed_at=None,
                   result_json="{}", created_at=None):
    """Insert a campaign_action row directly for test setup."""
    now = datetime.now(timezone.utc)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO campaign_actions "
        "(id, release_id, action_type, scheduled_for, status, payload_json, executed_at, result_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            action_id or str(uuid.uuid4()),
            release_id,
            action_type,
            scheduled_for or now.isoformat(),
            status,
            "{}",
            executed_at,
            result_json,
            created_at or now.isoformat(),
        ),
    )
    conn.commit()
    conn.close()


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_scheduler_diagnostics_401_without_key(monkeypatch, tmp_path):
    """Endpoint requires X-API-Key — must return 401 when key is absent."""
    client, _ = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics/scheduler")
    assert resp.status_code == 401


def test_scheduler_diagnostics_200_empty_db(monkeypatch, tmp_path):
    """Empty DB returns 200 with correct shape and empty collections."""
    client, _ = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics/scheduler", headers={"X-API-Key": _PLMKR_KEY})
    assert resp.status_code == 200
    body = resp.json()
    assert "timestamp"      in body
    assert "next_pending"   in body
    assert "last_completed" in body
    assert "counts_24h"     in body
    assert body["next_pending"]   == []
    assert body["last_completed"] == []
    assert body["counts_24h"]     == {}


def test_scheduler_diagnostics_next_pending_sorted(monkeypatch, tmp_path):
    """next_pending returns pending actions sorted by scheduled_for ASC, max 10."""
    client, db_path = _build_client(monkeypatch, tmp_path)
    now = datetime.now(timezone.utc)

    # Insert 3 pending actions with different scheduled times
    later  = (now + timedelta(hours=2)).isoformat()
    soon   = (now + timedelta(hours=1)).isoformat()
    soonest = (now + timedelta(minutes=30)).isoformat()

    _insert_action(db_path, action_id="a-later",   scheduled_for=later,   status="pending")
    _insert_action(db_path, action_id="a-soon",    scheduled_for=soon,    status="pending")
    _insert_action(db_path, action_id="a-soonest", scheduled_for=soonest, status="pending")
    # Insert a done action — must NOT appear in next_pending
    _insert_action(db_path, action_id="a-done",    scheduled_for=soonest, status="done")

    resp = client.get("/api/admin/diagnostics/scheduler", headers={"X-API-Key": _PLMKR_KEY})
    assert resp.status_code == 200
    pending = resp.json()["next_pending"]

    ids = [p["id"] for p in pending]
    assert "a-soonest" in ids
    assert "a-soon"    in ids
    assert "a-later"   in ids
    assert "a-done"    not in ids
    # Verify ascending order
    assert ids.index("a-soonest") < ids.index("a-soon") < ids.index("a-later")
    # Verify required fields present
    for item in pending:
        assert "id"            in item
        assert "release_id"    in item
        assert "action_type"   in item
        assert "scheduled_for" in item


def test_scheduler_diagnostics_last_completed_sorted(monkeypatch, tmp_path):
    """last_completed returns done/failed actions sorted by executed_at DESC, max 20."""
    client, db_path = _build_client(monkeypatch, tmp_path)
    now = datetime.now(timezone.utc)

    older  = (now - timedelta(hours=2)).isoformat()
    newer  = (now - timedelta(hours=1)).isoformat()
    result = json.dumps({"status": "ok", "sent": 2})

    _insert_action(db_path, action_id="c-older",  status="done",   executed_at=older,  result_json=result)
    _insert_action(db_path, action_id="c-newer",  status="done",   executed_at=newer,  result_json=result)
    _insert_action(db_path, action_id="c-failed", status="failed", executed_at=older,  result_json=json.dumps({"error": "oops"}))
    # Pending must NOT appear in last_completed
    _insert_action(db_path, action_id="c-pend",   status="pending")

    resp = client.get("/api/admin/diagnostics/scheduler", headers={"X-API-Key": _PLMKR_KEY})
    assert resp.status_code == 200
    completed = resp.json()["last_completed"]

    ids = [c["id"] for c in completed]
    assert "c-newer"  in ids
    assert "c-older"  in ids
    assert "c-failed" in ids
    assert "c-pend"   not in ids
    # Verify descending order (newer first)
    assert ids.index("c-newer") < ids.index("c-older")
    # Verify fields
    for item in completed:
        assert "id"           in item
        assert "release_id"   in item
        assert "action_type"  in item
        assert "executed_at"  in item
        assert "status"       in item
        assert "result"       in item


def test_scheduler_diagnostics_counts_24h_by_status(monkeypatch, tmp_path):
    """counts_24h groups campaign_actions by status for rows created in the last 24 hours."""
    client, db_path = _build_client(monkeypatch, tmp_path)
    now = datetime.now(timezone.utc)

    within_24h  = (now - timedelta(hours=12)).isoformat()
    outside_24h = (now - timedelta(hours=30)).isoformat()

    # 2 pending within 24h
    _insert_action(db_path, action_id="cnt-p1", status="pending", created_at=within_24h)
    _insert_action(db_path, action_id="cnt-p2", status="pending", created_at=within_24h)
    # 1 done within 24h
    _insert_action(db_path, action_id="cnt-d1", status="done",    created_at=within_24h)
    # 1 old pending — must NOT appear in 24h counts
    _insert_action(db_path, action_id="cnt-old", status="pending", created_at=outside_24h)

    resp = client.get("/api/admin/diagnostics/scheduler", headers={"X-API-Key": _PLMKR_KEY})
    assert resp.status_code == 200
    counts = resp.json()["counts_24h"]

    assert counts.get("pending") == 2
    assert counts.get("done")    == 1
    # Old row must not be counted
    assert counts.get("pending", 0) == 2
