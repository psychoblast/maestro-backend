"""
Unit tests for pitch_service.py — mock Gmail client, no real credentials needed.

Run with:  python3 -m pytest tests/ -v
"""

import asyncio
import json
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point pitch_service at a throw-away SQLite DB for each test."""
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("DATABASE_URL", "")          # force SQLite
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    # Re-import so module-level _DB_PATH picks up the new env var
    import importlib
    import pitch_service
    importlib.reload(pitch_service)
    pitch_service.init_pitch_db()
    yield db


@pytest.fixture()
def ps():
    import pitch_service
    return pitch_service


# ── Helper ────────────────────────────────────────────────────────────────────

def _seed_curator(ps, curator_id="cur-test-001", tier="B"):
    c = {
        "id":            curator_id,
        "name":          "Test Curator",
        "outlet":        "Test Playlist",
        "genres":        ["indie", "pop"],
        "tier":          tier,
        "contact_email": "curator@example.com",
        "notes":         "",
        "response_rate": 0.0,
    }
    ps._db_upsert_curator(c)
    return c


def _seed_artist(ps, artist_id="artist-test-001"):
    data = {
        "artist_id":   artist_id,
        "artist_name": "Test Artist",
        "genre":       "indie pop",
        "bio":         "An emerging indie pop artist from London.",
    }
    ps._save_artist_data(artist_id, data)
    return data


# ── 1.1 Gmail OAuth ───────────────────────────────────────────────────────────

def test_gmail_status_no_tokens(ps):
    result = ps.gmail_status("no-artist")
    assert result == {"connected": False, "artist_id": "no-artist"}


def test_gmail_status_with_tokens(ps):
    ps._save_gmail_tokens("artist-abc", {"access_token": "tok123"})
    result = ps.gmail_status("artist-abc")
    assert result["connected"] is True


def test_save_and_load_gmail_tokens(ps):
    tokens = {"access_token": "aaa", "refresh_token": "bbb", "expires_at": None}
    ps._save_gmail_tokens("artist-xyz", tokens)
    loaded = ps._load_gmail_tokens("artist-xyz")
    assert loaded["access_token"] == "aaa"
    assert loaded["refresh_token"] == "bbb"


# ── 1.2 sendEmail() ───────────────────────────────────────────────────────────

def test_send_email_no_tokens_raises(ps):
    with pytest.raises(ps.GmailNotConnected):
        asyncio.run(ps.send_email("no-artist", "to@example.com", "Subject", "Body"))


def test_send_email_calls_gmail_api(ps):
    """
    Mock _get_gmail_service() so no real credentials are needed.
    Confirms send_email() calls users().messages().send() and returns message_id.
    """
    mock_service = MagicMock()
    mock_send    = MagicMock()
    mock_send.execute.return_value = {"id": "msg-abc", "threadId": "thr-xyz"}
    mock_service.users.return_value.messages.return_value.send.return_value = mock_send

    with patch.object(ps, "_get_gmail_service", return_value=mock_service):
        result = asyncio.run(ps.send_email("artist-1", "to@example.com", "Hello", "World"))

    assert result["message_id"] == "msg-abc"
    assert result["thread_id"]  == "thr-xyz"
    assert result["status"]     == "sent"
    mock_service.users().messages().send.assert_called_once()


# ── 1.3 Curator CRUD ─────────────────────────────────────────────────────────

def test_create_and_get_curator(ps):
    c = _seed_curator(ps)
    fetched = ps._db_get_curator("cur-test-001")
    assert fetched["name"]   == "Test Curator"
    assert fetched["tier"]   == "B"
    assert isinstance(fetched["genres"], list)
    assert "indie" in fetched["genres"]


def test_list_curators_filter_tier(ps):
    _seed_curator(ps, "cur-a", tier="A")
    _seed_curator(ps, "cur-c", tier="C")
    a_list = ps._db_list_curators(tier="A")
    assert all(c["tier"] == "A" for c in a_list)
    assert len(a_list) == 1


def test_list_curators_filter_genre(ps):
    _seed_curator(ps)   # genres: indie, pop
    results = ps._db_list_curators(genre="indie")
    assert len(results) == 1
    results_miss = ps._db_list_curators(genre="country")
    assert len(results_miss) == 0


# ── 1.3 Pitch CRUD ───────────────────────────────────────────────────────────

def test_create_and_get_pitch(ps):
    _seed_curator(ps)
    pitch = {
        "id":         "pitch-001",
        "artist_id":  "artist-001",
        "curator_id": "cur-test-001",
        "status":     "draft",
        "subject":    "Great track for your playlist",
        "body":       "Hi, please check out my new single.",
    }
    ps._db_create_pitch(pitch)
    fetched = ps._db_get_pitch("pitch-001")
    assert fetched["status"]  == "draft"
    assert fetched["subject"] == "Great track for your playlist"


def test_update_pitch_status(ps):
    _seed_curator(ps)
    ps._db_create_pitch({
        "id": "pitch-002", "artist_id": "a1", "curator_id": "cur-test-001",
        "status": "draft", "subject": "Sub", "body": "Body",
    })
    ps._db_update_pitch("pitch-002", {"status": "sent"})
    p = ps._db_get_pitch("pitch-002")
    assert p["status"] == "sent"


def test_list_pitches_for_artist(ps):
    _seed_curator(ps)
    ps._db_create_pitch({
        "id": "p1", "artist_id": "artist-A", "curator_id": "cur-test-001",
        "status": "draft", "subject": "S1", "body": "B1",
    })
    ps._db_create_pitch({
        "id": "p2", "artist_id": "artist-B", "curator_id": "cur-test-001",
        "status": "draft", "subject": "S2", "body": "B2",
    })
    a_pitches = ps._db_list_pitches("artist-A")
    assert len(a_pitches) == 1
    assert a_pitches[0]["id"] == "p1"


def test_add_and_list_interactions(ps):
    _seed_curator(ps)
    ps._db_create_pitch({
        "id": "p3", "artist_id": "a1", "curator_id": "cur-test-001",
        "status": "sent", "subject": "S", "body": "B",
    })
    ps._db_add_interaction({
        "id":        "int-001",
        "pitch_id":  "p3",
        "direction": "inbound",
        "content":   "Thanks, we love it!",
        "sentiment": "positive",
    })
    interactions = ps._db_list_interactions("p3")
    assert len(interactions) == 1
    assert interactions[0]["sentiment"] == "positive"


# ── 1.5 generatePitchEmail() ─────────────────────────────────────────────────

def test_generate_pitch_email_returns_valid_shape(ps):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(
        text='{"subject":"Check out Test Artist","body":"Hi, please listen.","suggested_followup_days":5}'
    )]
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_resp
        artist  = {"artist_name": "Test Artist", "genre": "indie"}
        curator = _seed_curator(ps)
        result  = asyncio.run(ps.generate_pitch_email(artist, {"name": "New Single"}, curator))

    assert "subject" in result
    assert "body"    in result
    assert "suggested_followup_days" in result


# ── 1.6 sendPitchEmails() batch ──────────────────────────────────────────────

def test_batch_pitch_gmail_not_connected(ps):
    """When Gmail is not connected, all sends fail gracefully."""
    _seed_curator(ps)
    _seed_artist(ps)

    mock_draft = MagicMock()
    mock_draft.content = [MagicMock(
        text='{"subject":"S","body":"B","suggested_followup_days":5}'
    )]

    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_draft
        with patch.object(ps, "_get_gmail_service", side_effect=ps.GmailNotConnected):
            from fastapi.testclient import TestClient
            from fastapi import FastAPI
            test_app = FastAPI()
            test_app.include_router(ps.router)
            client = TestClient(test_app)
            resp = client.post("/api/pitches/batch", json={
                "artist_id":   "artist-test-001",
                "curator_ids": ["cur-test-001"],
                "track_metadata": {"name": "My Song"},
            })

    assert resp.status_code == 200
    data = resp.json()
    assert data["sent"]   == 0
    assert data["failed"] == 1
    assert len(data["errors"]) == 1


# ── 1.9 Follow-up threshold logic ────────────────────────────────────────────

def test_followup_no_pitches(ps):
    """No sent pitches → empty list."""
    results = ps._get_pitches_needing_followup()
    assert results == []


def test_followup_recent_pitch_not_triggered(ps):
    """Pitch sent today → not in follow-up list (day 0, not in thresholds)."""
    _seed_curator(ps)
    now_str = "2026-05-08T10:00:00"
    ps._db_create_pitch({
        "id": "fu-p1", "artist_id": "a1", "curator_id": "cur-test-001",
        "status": "sent", "subject": "S", "body": "B",
    })
    ps._db_update_pitch("fu-p1", {"sent_at": now_str})
    results = ps._get_pitches_needing_followup()
    assert all(r["id"] != "fu-p1" for r in results)


# ── Deterministic idempotency key ─────────────────────────────────────────────

def test_idempotency_key_blocks_duplicate_pitch(ps):
    """Inserting two pitches with the same idempotency_key raises IntegrityError."""
    import hashlib, sqlite3
    from datetime import datetime, timezone
    send_window = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = hashlib.sha256(f"a1:cur-test-001:{send_window}".encode()).hexdigest()

    ps._db_create_pitch({
        "id": "idem-1", "artist_id": "a1", "curator_id": "cur-test-001",
        "status": "sent", "subject": "S", "body": "B",
        "idempotency_key": key,
    })
    with pytest.raises(sqlite3.IntegrityError):
        ps._db_create_pitch({
            "id": "idem-2", "artist_id": "a1", "curator_id": "cur-test-001",
            "status": "sent", "subject": "S", "body": "B",
            "idempotency_key": key,  # same key → UNIQUE violation
        })


def test_different_day_key_allows_second_pitch(ps):
    """Same artist+curator on a different calendar date produces a distinct
    idempotency key, so a day-N+1 retry is not blocked by the UNIQUE constraint.

    Uses the exact key formula from pitch_service (_build_idempotency_key is
    inline — sha256(artist_id:curator_id:YYYY-MM-DD)) and exercises the real
    DB schema, not just hash arithmetic.
    """
    import hashlib, sqlite3
    _seed_curator(ps)
    key_day1 = hashlib.sha256(b"a1:cur-test-001:2026-05-10").hexdigest()
    key_day2 = hashlib.sha256(b"a1:cur-test-001:2026-05-11").hexdigest()

    ps._db_create_pitch({
        "id": "idem-day1", "artist_id": "a1", "curator_id": "cur-test-001",
        "status": "sent", "subject": "S", "body": "B",
        "idempotency_key": key_day1,
    })
    # Day 2 key must not collide with day 1 — should not raise IntegrityError
    ps._db_create_pitch({
        "id": "idem-day2", "artist_id": "a1", "curator_id": "cur-test-001",
        "status": "sent", "subject": "S", "body": "B",
        "idempotency_key": key_day2,
    })
    assert ps._db_get_pitch("idem-day1") is not None
    assert ps._db_get_pitch("idem-day2") is not None
