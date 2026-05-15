"""
IT-A1 — Artist Onboarding Flow Integration Tests

Covers the end-to-end path from artist seed through first pitch send and debrief:
  1. Seeded artist profile is present and correct in the DB
  2. Curator creation via POST /api/curators
  3. Pitch generation calls real _anthropic_call_with_retry → anthropic stats increment
  4. Batch send runs real send_email + _gmail_execute_with_retry → both stats increment
  5. Sent pitch is retrievable with status=sent and gmail_thread_id set
  6. Inbox scan with a curator reply updates pitch status to replied

Mocks at API boundaries only (not service layer):
  - anthropic.Anthropic  (Anthropic SDK client constructor)
  - pitch_service._get_gmail_service  (Google API client factory)
"""

import json
import sqlite3
import uuid
from unittest.mock import MagicMock, patch

import pytest

from tests.integration.conftest import (
    build_app,
    make_claude_response,
    make_send_gmail_svc,
    mock_gmail_service,
    seed_artist,
    seed_gmail_tokens,
)


ARTIST_ID = "artist-onboard-001"

_PITCH_DRAFT = make_claude_response({
    "subject": "First Pitch — Onboarding Artist",
    "body":    "Hi! We'd love to be featured on your playlist.",
})
_CLASSIFY_POS = make_claude_response({
    "sentiment": "positive",
    "summary":   "Curator is enthusiastic and wants to add the track.",
})


@pytest.fixture()
def client(tmp_path):
    db = str(tmp_path / "onboarding.db")
    app = build_app(db)
    seed_artist(db, ARTIST_ID, artist_name="Onboarding Artist", genre="indie pop")
    seed_gmail_tokens(db, ARTIST_ID)
    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=True) as c:
        c._db = db
        yield c


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_seeded_artist_has_correct_profile(client):
    """Artist profile inserted by seed_artist is present with correct fields."""
    conn = sqlite3.connect(client._db)
    row  = conn.execute(
        "SELECT data FROM artists WHERE artist_id=?", (ARTIST_ID,)
    ).fetchone()
    conn.close()
    assert row is not None, "Artist not found in DB"
    profile = json.loads(row[0])
    assert profile["artist_id"] == ARTIST_ID
    assert profile["genre"] == "indie pop"
    assert profile["artist_name"] == "Onboarding Artist"


def test_create_curator_returns_id_and_tier(client):
    """POST /api/curators creates a record and returns a usable ID."""
    r = client.post("/api/curators", json={
        "name":          "Jordan Lee",
        "outlet":        "Indie Discovery",
        "genres":        ["indie", "pop"],
        "tier":          "B",
        "contact_email": "jordan@example.com",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert "id" in body
    assert body["tier"] == "B"
    assert body["outlet"] == "Indie Discovery"


def test_pitch_generation_increments_anthropic_stats(client):
    """POST /api/pitches/generate calls _anthropic_call_with_retry → stats.total increases."""
    from anthropic_utils import get_anthropic_stats

    r = client.post("/api/curators", json={
        "name": "Casey B.", "outlet": "Chill Vibes",
        "genres": ["indie"], "tier": "B",
        "contact_email": "casey@example.com",
    })
    assert r.status_code == 201
    curator_id = r.json()["id"]

    before = sum(v["total"] for v in get_anthropic_stats().values())

    with patch("anthropic.Anthropic") as mc:
        mc.return_value.messages.create.return_value = _PITCH_DRAFT
        r = client.post("/api/pitches/generate", json={
            "artist_id":  ARTIST_ID,
            "curator_id": curator_id,
        })
    assert r.status_code == 200, r.text
    body = r.json()
    assert "subject" in body and "body" in body

    after = sum(v["total"] for v in get_anthropic_stats().values())
    assert after > before, "anthropic_stats.total must increase after pitch generation"


def test_batch_send_increments_anthropic_and_gmail_stats(client):
    """POST /api/pitches/batch runs real send_email path → both counters increment."""
    import pitch_service
    from anthropic_utils import get_anthropic_stats

    r = client.post("/api/curators", json={
        "name": "River P.", "outlet": "New Wave Radio",
        "genres": ["pop"], "tier": "A",
        "contact_email": "river@example.com",
    })
    assert r.status_code == 201
    curator_id = r.json()["id"]

    thread_id  = f"thread-{uuid.uuid4().hex[:8]}"
    mock_gmail = make_send_gmail_svc(thread_id)

    before_anthropic = sum(v["total"] for v in get_anthropic_stats().values())
    before_gmail     = sum(v["total"] for v in pitch_service.get_gmail_stats().values())

    with patch("anthropic.Anthropic") as mc, \
         patch("pitch_service._get_gmail_service", return_value=mock_gmail):
        mc.return_value.messages.create.return_value = _PITCH_DRAFT
        r = client.post("/api/pitches/batch", json={
            "artist_id":   ARTIST_ID,
            "curator_ids": [curator_id],
        })
    assert r.status_code == 200, r.text
    assert r.json()["sent"] == 1

    after_anthropic = sum(v["total"] for v in get_anthropic_stats().values())
    after_gmail     = sum(v["total"] for v in pitch_service.get_gmail_stats().values())

    assert after_anthropic > before_anthropic, "anthropic_stats should increment after batch send"
    assert after_gmail > before_gmail,         "gmail_stats should increment after batch send"


def test_sent_pitch_retrievable_with_correct_status_and_thread_id(client):
    """After batch send, GET /api/pitches/<id> returns status=sent and gmail_thread_id."""
    r = client.post("/api/curators", json={
        "name": "Skye M.", "outlet": "Morning Mood",
        "genres": ["acoustic"], "tier": "B",
        "contact_email": "skye@example.com",
    })
    assert r.status_code == 201
    curator_id = r.json()["id"]

    thread_id  = f"thread-{uuid.uuid4().hex[:8]}"
    mock_gmail = make_send_gmail_svc(thread_id)

    with patch("anthropic.Anthropic") as mc, \
         patch("pitch_service._get_gmail_service", return_value=mock_gmail):
        mc.return_value.messages.create.return_value = _PITCH_DRAFT
        r = client.post("/api/pitches/batch", json={
            "artist_id":   ARTIST_ID,
            "curator_ids": [curator_id],
        })
    assert r.status_code == 200
    pitch_id = r.json()["pitch_ids"][0]

    r = client.get(f"/api/pitches/{pitch_id}")
    assert r.status_code == 200, r.text
    pitch = r.json()
    assert pitch["status"] == "sent"
    assert pitch["gmail_thread_id"] == thread_id


def test_inbox_scan_marks_pitch_replied(client):
    """Full debrief: inbox scan with a matching curator reply updates pitch to replied."""
    from anthropic_utils import get_anthropic_stats

    r = client.post("/api/curators", json={
        "name": "Dana K.", "outlet": "Folk & Indie Blog",
        "genres": ["folk", "indie"], "tier": "B",
        "contact_email": "dana@example.com",
    })
    assert r.status_code == 201
    curator_id = r.json()["id"]

    thread_id  = f"thread-{uuid.uuid4().hex[:8]}"
    send_gmail = make_send_gmail_svc(thread_id)

    with patch("anthropic.Anthropic") as mc, \
         patch("pitch_service._get_gmail_service", return_value=send_gmail):
        mc.return_value.messages.create.return_value = _PITCH_DRAFT
        r = client.post("/api/pitches/batch", json={
            "artist_id":   ARTIST_ID,
            "curator_ids": [curator_id],
        })
    assert r.status_code == 200
    pitch_id = r.json()["pitch_ids"][0]

    inbox_svc = mock_gmail_service(
        thread_id,
        "First Pitch — Onboarding Artist",
        "Love it! Adding to the playlist.",
    )
    before = sum(v["total"] for v in get_anthropic_stats().values())

    with patch("pitch_service._get_gmail_service", return_value=inbox_svc), \
         patch("anthropic.Anthropic") as mc:
        mc.return_value.messages.create.return_value = _CLASSIFY_POS
        r = client.post(f"/api/inbox/scan?artist_id={ARTIST_ID}")
    assert r.status_code == 200, r.text
    scan = r.json()
    assert scan["matched"] == 1

    after = sum(v["total"] for v in get_anthropic_stats().values())
    assert after > before, "classify call should increment anthropic_stats"

    r = client.get(f"/api/pitches/{pitch_id}")
    assert r.json()["status"] == "replied"
