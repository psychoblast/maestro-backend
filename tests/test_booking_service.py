"""
Unit tests for booking_service.py — no real credentials needed, Gmail mocked.

Run with:  python3 -m pytest tests/ -v
"""

import json
import importlib
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point booking_service at a throw-away SQLite DB for each test."""
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import booking_service
    importlib.reload(booking_service)
    booking_service.init_booking_db()
    yield db


@pytest.fixture()
def bs():
    import booking_service
    return booking_service


# ── Helpers ───────────────────────────────────────────────────────────────────

def _seed_venue(bs, contact_id="bk-test-001", tier="B", venue_type="venue"):
    c = {
        "id":               contact_id,
        "name":             "Test Booker",
        "venue_or_festival":"Test Venue",
        "type":             venue_type,
        "city":             "London",
        "country":          "UK",
        "capacity":         500,
        "genres":           ["indie", "rock"],
        "tier":             tier,
        "contact_email":    "booking@example.com",
        "notes":            "",
        "response_rate":    0.0,
    }
    bs._db_upsert_booking_contact(c)
    return c


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_create_and_get_booking_contact(bs):
    _seed_venue(bs)
    c = bs._db_get_booking_contact("bk-test-001")
    assert c["name"] == "Test Booker"
    assert c["capacity"] == 500
    assert c["genres"] == ["indie", "rock"]


def test_list_booking_contacts_filter_tier(bs):
    _seed_venue(bs, "bk-a-001", tier="A")
    _seed_venue(bs, "bk-c-001", tier="C")
    a_list = bs._db_list_booking_contacts(tier="A")
    assert len(a_list) == 1
    assert a_list[0]["id"] == "bk-a-001"


def test_list_booking_contacts_filter_type(bs):
    _seed_venue(bs, "bk-venue-001", venue_type="venue")
    _seed_venue(bs, "bk-fest-001", venue_type="festival")
    fests = bs._db_list_booking_contacts(contact_type="festival")
    assert len(fests) == 1
    assert fests[0]["id"] == "bk-fest-001"


def test_create_and_get_booking_inquiry(bs):
    _seed_venue(bs)
    i_id = "inq-test-001"
    bs._db_create_booking_inquiry({
        "id":         i_id,
        "artist_id":  "artist-001",
        "contact_id": "bk-test-001",
        "status":     "draft",
        "subject":    "Booking inquiry — Test Artist",
        "body":       "Hi, we'd love to play your venue.",
    })
    fetched = bs._db_get_booking_inquiry(i_id)
    assert fetched["subject"] == "Booking inquiry — Test Artist"
    assert fetched["status"] == "draft"


def test_update_booking_inquiry_status(bs):
    _seed_venue(bs)
    i_id = "inq-update-001"
    bs._db_create_booking_inquiry({
        "id": i_id, "artist_id": "artist-001", "contact_id": "bk-test-001",
        "status": "draft", "subject": "Test", "body": "Body",
    })
    bs._db_update_booking_inquiry(i_id, {"status": "sent"})
    assert bs._db_get_booking_inquiry(i_id)["status"] == "sent"


def test_list_booking_inquiries_for_artist(bs):
    _seed_venue(bs)
    for i in range(3):
        bs._db_create_booking_inquiry({
            "id": f"inq-{i}", "artist_id": "artist-list",
            "contact_id": "bk-test-001", "status": "draft",
            "subject": f"Show {i}", "body": "Body",
        })
    results = bs._db_list_booking_inquiries("artist-list")
    assert len(results) == 3


def test_add_and_list_booking_interactions(bs):
    _seed_venue(bs)
    bs._db_create_booking_inquiry({
        "id": "inq-interact", "artist_id": "a1",
        "contact_id": "bk-test-001", "status": "sent",
        "subject": "Test", "body": "Body",
    })
    bs._db_add_booking_interaction({
        "id": "bi-001", "inquiry_id": "inq-interact",
        "direction": "outbound", "content": "Sent inquiry",
    })
    bs._db_add_booking_interaction({
        "id": "bi-002", "inquiry_id": "inq-interact",
        "direction": "inbound", "content": "Booker replied",
    })
    interactions = bs._db_list_booking_interactions("inq-interact")
    assert len(interactions) == 2
    assert interactions[0]["direction"] == "outbound"


def test_generate_booking_email_returns_valid_shape(bs):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(
        text='{"subject":"Booking inquiry","body":"We would love to play.","suggested_followup_days":14}'
    )]
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.return_value = mock_resp
        result = asyncio.run(bs.generate_booking_email(
            {"artist_name": "Test Artist", "genre": "indie"},
            {"available_dates": ["2026-08-15"], "highlight": "100k monthly listeners"},
            _seed_venue(bs),
        ))
    assert "subject" in result
    assert "body" in result
    assert "suggested_followup_days" in result


def test_batch_booking_gmail_not_connected(bs):
    _seed_venue(bs)
    with patch.object(bs, "_load_artist_data", return_value={"artist_name": "Test"}):
        with patch("pitch_service.send_email", new=AsyncMock(side_effect=Exception("GmailNotConnected"))):
            with patch.object(bs, "generate_booking_email", new=AsyncMock(
                return_value={"subject": "Test", "body": "Body", "suggested_followup_days": 14}
            )):
                req = bs.BatchBookingRequest(
                    artist_id="artist-001",
                    contact_ids=["bk-test-001"],
                    show_context={},
                )
                result = asyncio.run(bs.send_booking_emails(req))
    assert result["failed"] == 1


def test_booking_followup_not_triggered_for_fresh_inquiry(bs):
    _seed_venue(bs)
    bs._db_create_booking_inquiry({
        "id": "inq-fresh", "artist_id": "artist-001",
        "contact_id": "bk-test-001", "status": "sent",
        "subject": "Fresh inquiry", "body": "Body",
    })
    now_str = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(bs._DB_PATH))
    conn.execute("UPDATE booking_inquiries SET sent_at=? WHERE id='inq-fresh'", (now_str,))
    conn.commit()
    conn.close()
    result = bs._get_booking_inquiries_needing_followup("artist-001")
    assert result == []


def test_booking_contact_city_filter(bs):
    _seed_venue(bs, "bk-lon-001")  # city=London
    c2 = {**_seed_venue(bs, "bk-nyc-001"), "city": "New York"}
    bs._db_upsert_booking_contact(c2)
    london_list = bs._db_list_booking_contacts(city="London")
    assert all("London" in c["city"] for c in london_list)
