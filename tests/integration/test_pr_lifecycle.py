"""
IT.2 — Phase 2 PR Lifecycle Integration Test

Full flow (one test function, sequential assertions):
  1. Create PR contact via POST /api/pr-contacts
  2. Generate PR email (Claude mocked) via POST /api/pr-outreach/generate
  3. Batch send → outreach saved with status=sent + gmail_thread_id recorded
  4. Mock Gmail inbox scan + Claude classify → status=replied
  5. Assert PRInteraction logged with direction=inbound
"""

import json
import uuid
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from tests.integration.conftest import mock_gmail_service


ARTIST_ID = "artist-pr-001"


@pytest.fixture()
def client(tmp_path):
    from tests.integration.conftest import build_app, seed_artist, seed_gmail_tokens
    from fastapi.testclient import TestClient
    db = str(tmp_path / "pr_lifecycle.db")
    app = build_app(db)
    seed_artist(db, ARTIST_ID)
    seed_gmail_tokens(db, ARTIST_ID)
    with TestClient(app, raise_server_exceptions=True) as c:
        c._db = db
        yield c


# ── Claude mock helpers ───────────────────────────────────────────────────────

def _claude_pr_response():
    m = MagicMock()
    m.content = [MagicMock(text=json.dumps({
        "subject": "Feature request — Integration Artist's new EP",
        "body":    "Hi, we'd love to have you cover our upcoming EP release.",
    }))]
    return m


def _claude_classify_response(sentiment="positive"):
    m = MagicMock()
    m.content = [MagicMock(text=json.dumps({
        "sentiment": sentiment,
        "summary":   "Press contact expressed interest in covering the release.",
    }))]
    return m


# ── Lifecycle test ────────────────────────────────────────────────────────────

def test_pr_lifecycle_full(client):
    # ── Step 1: Create PR contact ─────────────────────────────────────────────
    r = client.post("/api/pr-contacts", json={
        "name":          "Alex Rivera",
        "outlet_type":   "blog",
        "outlet_name":   "Indie Pulse Blog",
        "genres":        ["indie", "alternative"],
        "tier":          "B",
        "contact_email": "alex@indiepulse.example.com",
        "beat":          "emerging artists",
    })
    assert r.status_code == 201, r.text
    contact = r.json()
    contact_id = contact["id"]
    assert contact["tier"] == "B"

    # ── Step 2: Generate PR email (Claude mocked) ─────────────────────────────
    mock_resp = _claude_pr_response()
    with patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.return_value = mock_resp
        r = client.post("/api/pr-outreach/generate", json={
            "artist_id":  ARTIST_ID,
            "contact_id": contact_id,
        })
    assert r.status_code == 200, r.text
    generated = r.json()
    assert "subject" in generated
    assert "body" in generated

    # ── Step 3: Batch send (mocked Claude + mocked Gmail send) ────────────────
    thread_id  = f"thread-pr-{uuid.uuid4().hex[:8]}"
    mock_send  = AsyncMock(return_value={"message_id": "pr-msg-001", "thread_id": thread_id})
    mock_email = _claude_pr_response()

    with patch("anthropic.Anthropic") as mock_claude, \
         patch("pitch_service.send_email", mock_send):
        mock_claude.return_value.messages.create.return_value = mock_email
        r = client.post("/api/pr-outreach/batch", json={
            "artist_id":   ARTIST_ID,
            "contact_ids": [contact_id],
        })
    assert r.status_code == 200, r.text
    batch_result = r.json()
    assert batch_result["sent"] == 1
    assert batch_result["failed"] == 0
    outreach_id = batch_result["outreach_ids"][0]

    # ── Step 4: Assert outreach has status=sent + thread_id recorded ──────────
    r = client.get(f"/api/pr-outreach/{outreach_id}")
    assert r.status_code == 200, r.text
    outreach = r.json()
    assert outreach["status"] == "sent"
    assert outreach["gmail_thread_id"] == thread_id

    # ── Step 5: Simulate inbox scan — one reply matching thread_id ────────────
    gmail_svc     = mock_gmail_service(thread_id, generated["subject"], "Yes, I'd love to cover this!")
    classify_resp = _claude_classify_response("positive")

    with patch("pitch_service._get_gmail_service", return_value=gmail_svc), \
         patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.return_value = classify_resp
        r = client.post(f"/api/pr-outreach/scan?artist_id={ARTIST_ID}")
    assert r.status_code == 200, r.text
    scan = r.json()
    assert scan["scanned"] >= 1
    assert scan["matched"] == 1
    assert scan["classified"][0]["sentiment"] == "positive"

    # ── Step 6: Assert outreach status=replied + interaction logged ───────────
    r = client.get(f"/api/pr-outreach/{outreach_id}")
    outreach = r.json()
    assert outreach["status"] == "replied"

    interactions = outreach.get("interactions", [])
    assert any(i["direction"] == "inbound" for i in interactions), (
        "Expected an inbound PRInteraction after reply detection"
    )
