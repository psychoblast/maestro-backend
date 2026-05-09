"""
IT.1 — Phase 1 Pitch Lifecycle Integration Test

Full flow (one test function, sequential assertions):
  1. Create curator via POST /api/curators
  2. Generate pitch email (Claude mocked) via POST /api/pitches/generate
  3. Create Pitch record with status=draft
  4. Mock Gmail send → status=sent + gmail_thread_id recorded
  5. Mock Gmail inbox scan + Claude classify → status=replied
  6. Assert PitchInteraction logged with direction=inbound
"""

import json
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from tests.integration.conftest import mock_gmail_service


ARTIST_ID = "artist-pitch-001"


@pytest.fixture()
def client(tmp_path):
    from tests.integration.conftest import build_app, seed_artist, seed_gmail_tokens
    from fastapi.testclient import TestClient
    db = str(tmp_path / "pitch_lifecycle.db")
    app = build_app(db)
    seed_artist(db, ARTIST_ID)
    seed_gmail_tokens(db, ARTIST_ID)
    with TestClient(app, raise_server_exceptions=True) as c:
        c._db = db
        yield c


# ── Claude mock helpers ───────────────────────────────────────────────────────

def _claude_pitch_response():
    m = MagicMock()
    m.content = [MagicMock(text=json.dumps({
        "subject": "Playlist pitch — Integration Artist",
        "body":    "Hi, we'd love to have you feature our new single.",
    }))]
    return m


def _claude_classify_response(sentiment="positive"):
    m = MagicMock()
    m.content = [MagicMock(text=json.dumps({
        "sentiment": sentiment,
        "summary":   "Curator expressed strong interest.",
    }))]
    return m


# ── Lifecycle test ────────────────────────────────────────────────────────────

def test_pitch_lifecycle_full(client):
    # ── Step 1: Create curator ────────────────────────────────────────────────
    r = client.post("/api/curators", json={
        "name":          "Jordan Lee",
        "outlet":        "Indie Discovery Playlist",
        "genres":        ["indie", "pop"],
        "tier":          "B",
        "contact_email": "jordan@example.com",
    })
    assert r.status_code == 201, r.text
    curator = r.json()
    curator_id = curator["id"]
    assert curator["tier"] == "B"

    # ── Step 2: Generate pitch email (Claude mocked) ──────────────────────────
    mock_resp = _claude_pitch_response()
    with patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.return_value = mock_resp
        r = client.post("/api/pitches/generate", json={
            "artist_id":  ARTIST_ID,
            "curator_id": curator_id,
        })
    assert r.status_code == 200, r.text
    generated = r.json()
    assert "subject" in generated
    assert "body" in generated

    # ── Step 3: Batch send (mocked Claude + mocked Gmail send) ────────────────
    thread_id  = f"thread-{uuid.uuid4().hex[:8]}"
    mock_send  = AsyncMock(return_value={"message_id": "msg-001", "thread_id": thread_id})
    mock_pitch = _claude_pitch_response()

    with patch("anthropic.Anthropic") as mock_claude, \
         patch("pitch_service.send_email", mock_send):
        mock_claude.return_value.messages.create.return_value = mock_pitch
        r = client.post("/api/pitches/batch", json={
            "artist_id":   ARTIST_ID,
            "curator_ids": [curator_id],
        })
    assert r.status_code == 200, r.text
    batch_result = r.json()
    assert batch_result["sent"] == 1
    assert batch_result["failed"] == 0
    pitch_id = batch_result["pitch_ids"][0]

    # ── Step 4: Assert pitch now has status=sent and thread_id recorded ───────
    r = client.get(f"/api/pitches/{pitch_id}")
    assert r.status_code == 200, r.text
    pitch = r.json()
    assert pitch["status"] == "sent"
    assert pitch["gmail_thread_id"] == thread_id

    # ── Step 5: Simulate inbox scan — one reply matching thread_id ────────────
    gmail_svc       = mock_gmail_service(thread_id, generated["subject"], "Love it! I'm interested.")
    classify_resp   = _claude_classify_response("positive")

    with patch("pitch_service._get_gmail_service", return_value=gmail_svc), \
         patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.return_value = classify_resp
        r = client.post(f"/api/inbox/scan?artist_id={ARTIST_ID}")
    assert r.status_code == 200, r.text
    scan = r.json()
    assert scan["scanned"] >= 1
    assert scan["matched"] == 1
    assert scan["classified"][0]["sentiment"] == "positive"

    # ── Step 6: Assert pitch status=replied + interaction logged ──────────────
    r = client.get(f"/api/pitches/{pitch_id}")
    pitch = r.json()
    assert pitch["status"] == "replied"

    interactions = pitch.get("interactions", [])
    assert any(i["direction"] == "inbound" for i in interactions), (
        "Expected an inbound PitchInteraction after reply detection"
    )
