"""
Unit tests for pr_service.py — no real credentials needed, Gmail mocked.

Run with:  python3 -m pytest tests/ -v
"""

import json
import importlib
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point pr_service at a throw-away SQLite DB for each test."""
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import pr_service
    importlib.reload(pr_service)
    pr_service.init_pr_db()
    yield db


@pytest.fixture()
def ps():
    import pr_service
    return pr_service


# ── Helpers ───────────────────────────────────────────────────────────────────

def _seed_pr_contact(ps, contact_id="pr-test-001", tier="B", outlet_type="blog"):
    c = {
        "id":            contact_id,
        "name":          "Test Journalist",
        "outlet_type":   outlet_type,
        "outlet_name":   "Test Blog",
        "genres":        ["indie", "pop"],
        "tier":          tier,
        "contact_email": "press@example.com",
        "beat":          "New Music",
        "notes":         "",
        "response_rate": 0.0,
    }
    ps._db_upsert_pr_contact(c)
    return c


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_create_and_get_pr_contact(ps):
    _seed_pr_contact(ps)
    c = ps._db_get_pr_contact("pr-test-001")
    assert c["name"] == "Test Journalist"
    assert c["tier"] == "B"
    assert c["genres"] == ["indie", "pop"]


def test_list_pr_contacts_filter_tier(ps):
    _seed_pr_contact(ps, "pr-a-001", tier="A")
    _seed_pr_contact(ps, "pr-c-001", tier="C")
    a_list = ps._db_list_pr_contacts(tier="A")
    assert len(a_list) == 1
    assert a_list[0]["id"] == "pr-a-001"


def test_list_pr_contacts_filter_outlet_type(ps):
    _seed_pr_contact(ps, "pr-blog-001", outlet_type="blog")
    _seed_pr_contact(ps, "pr-pod-001", outlet_type="podcast")
    pods = ps._db_list_pr_contacts(outlet_type="podcast")
    assert len(pods) == 1
    assert pods[0]["id"] == "pr-pod-001"


def test_create_and_get_pr_outreach(ps):
    _seed_pr_contact(ps)
    o_id = "out-test-001"
    o    = {
        "id":         o_id,
        "artist_id":  "artist-001",
        "contact_id": "pr-test-001",
        "status":     "draft",
        "subject":    "New single from Test Artist",
        "body":       "Hi, we have a new track for you.",
    }
    ps._db_create_pr_outreach(o)
    fetched = ps._db_get_pr_outreach(o_id)
    assert fetched["subject"] == "New single from Test Artist"
    assert fetched["status"] == "draft"


def test_update_pr_outreach_status(ps):
    _seed_pr_contact(ps)
    o_id = "out-update-001"
    ps._db_create_pr_outreach({
        "id": o_id, "artist_id": "artist-001", "contact_id": "pr-test-001",
        "status": "draft", "subject": "Test", "body": "Body",
    })
    ps._db_update_pr_outreach(o_id, {"status": "sent"})
    assert ps._db_get_pr_outreach(o_id)["status"] == "sent"


def test_list_pr_outreach_for_artist(ps):
    _seed_pr_contact(ps)
    for i in range(3):
        ps._db_create_pr_outreach({
            "id": f"out-{i}", "artist_id": "artist-list",
            "contact_id": "pr-test-001", "status": "draft",
            "subject": f"Pitch {i}", "body": "Body",
        })
    results = ps._db_list_pr_outreach("artist-list")
    assert len(results) == 3


def test_add_and_list_pr_interactions(ps):
    _seed_pr_contact(ps)
    ps._db_create_pr_outreach({
        "id": "out-interact", "artist_id": "a1",
        "contact_id": "pr-test-001", "status": "sent",
        "subject": "Test", "body": "Body",
    })
    ps._db_add_pr_interaction({
        "id": "int-001", "outreach_id": "out-interact",
        "direction": "outbound", "content": "Sent pitch",
    })
    ps._db_add_pr_interaction({
        "id": "int-002", "outreach_id": "out-interact",
        "direction": "inbound", "content": "Reply received",
    })
    interactions = ps._db_list_pr_interactions("out-interact")
    assert len(interactions) == 2
    assert interactions[0]["direction"] == "outbound"


def test_generate_pr_email_returns_valid_shape(ps):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text='{"subject":"Test subject","body":"Test body","suggested_followup_days":7}')]
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.return_value = mock_resp
        result = asyncio.run(ps.generate_pr_email(
            {"artist_name": "Test Artist", "genre": "indie"},
            {"name": "Test Single", "type": "single"},
            _seed_pr_contact(ps),
        ))
    assert "subject" in result
    assert "body" in result
    assert "suggested_followup_days" in result


def test_batch_pr_gmail_not_connected(ps):
    _seed_pr_contact(ps)
    with patch.object(ps, "_load_artist_data", return_value={"artist_name": "Test"}):
        with patch("pitch_service.send_email", new=AsyncMock(side_effect=Exception("GmailNotConnected"))):
            with patch.object(ps, "generate_pr_email", new=AsyncMock(
                return_value={"subject": "Test", "body": "Body", "suggested_followup_days": 7}
            )):
                req = ps.BatchPRRequest(
                    artist_id="artist-001",
                    contact_ids=["pr-test-001"],
                    release_context={},
                )
                result = asyncio.run(ps.send_pr_emails(req))
    assert result["failed"] == 1


def test_pr_followup_not_triggered_for_fresh_outreach(ps):
    import sqlite3
    _seed_pr_contact(ps)
    ps._db_create_pr_outreach({
        "id": "out-fresh", "artist_id": "artist-001",
        "contact_id": "pr-test-001", "status": "sent",
        "subject": "Fresh pitch", "body": "Body",
    })
    # Manually set sent_at to now (0 days old) — should NOT trigger
    import os
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(ps._DB_PATH))
    conn.execute("UPDATE pr_outreach SET sent_at=? WHERE id='out-fresh'", (now_str,))
    conn.commit()
    conn.close()
    result = ps._get_pr_outreach_needing_followup("artist-001")
    assert result == []
