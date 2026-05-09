"""
IT.4a — Phase 3 Social Post Lifecycle Integration Test

Full flow (one test function, sequential assertions):
  1. Generate post via POST /api/social/posts/generate (Claude mocked)
  2. Create post via POST /api/social/posts → status=draft
  3. Batch generate + schedule via POST /api/social/posts/batch
  4. Assert posts saved with correct platform + status=draft
  5. PATCH one post → status=posted
  6. List posts and verify filters work
"""

import json
from unittest.mock import MagicMock, patch

import pytest


ARTIST_ID = "artist-social-001"


@pytest.fixture()
def client(tmp_path):
    from tests.integration.conftest import build_app, seed_artist
    from fastapi.testclient import TestClient
    db = str(tmp_path / "social_lifecycle.db")
    app = build_app(db)
    seed_artist(db, ARTIST_ID)
    with TestClient(app, raise_server_exceptions=True) as c:
        c._db = db
        yield c


# ── Claude mock helpers ───────────────────────────────────────────────────────

def _claude_post_response(platform="twitter"):
    content_by_platform = {
        "twitter":   "New single out now 🎵 Stream it everywhere. Link in bio. #indiemusic",
        "instagram": "Super excited to share our new single with you all. This one was recorded live in one take.",
    }
    m = MagicMock()
    m.content = [MagicMock(text=json.dumps({
        "content":   content_by_platform.get(platform, "Check out our new music!"),
        "hashtags":  ["indiemusic", "newmusic"],
        "best_time": "18:00",
    }))]
    return m


def _claude_report_response():
    m = MagicMock()
    m.content = [MagicMock(text=json.dumps({
        "headline":        "Strong social week with 3 posts published",
        "highlights":      ["3 posts scheduled", "Twitter engagement up", "Instagram reach growing"],
        "insights":        "Social activity is building momentum. Consistent posting schedule is paying off.",
        "recommendations": "1. Post at peak times. 2. Engage with comments within 2 hours.",
        "momentum_score":  7,
    }))]
    return m


# ── Lifecycle test ────────────────────────────────────────────────────────────

def test_social_lifecycle_full(client):
    # ── Step 1: Generate a single post (Claude mocked) ────────────────────────
    mock_resp = _claude_post_response("twitter")
    with patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.return_value = mock_resp
        r = client.post("/api/social/posts/generate", json={
            "artist_id": ARTIST_ID,
            "platform":  "twitter",
            "context":   {"release": "new single"},
            "tone":      "authentic",
        })
    assert r.status_code == 200, r.text
    generated = r.json()
    assert "content" in generated
    assert len(generated["content"]) <= 280  # Twitter limit

    # ── Step 2: Create post manually → status=draft ────────────────────────
    r = client.post("/api/social/posts", json={
        "artist_id":   ARTIST_ID,
        "platform":    "twitter",
        "content":     generated["content"],
        "status":      "draft",
        "scheduled_at": "2026-05-15T18:00:00",
    })
    assert r.status_code == 201, r.text
    manual_post = r.json()
    manual_post_id = manual_post["id"]
    assert manual_post["status"] == "draft"

    # ── Step 3: Batch generate posts (Claude mocked) ──────────────────────────
    mock_twitter = _claude_post_response("twitter")
    mock_instagram = _claude_post_response("instagram")
    call_count = [0]

    def mock_create(**kwargs):
        result = mock_twitter if call_count[0] % 2 == 0 else mock_instagram
        call_count[0] += 1
        return result

    with patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.side_effect = mock_create
        r = client.post("/api/social/posts/batch", json={
            "artist_id":         ARTIST_ID,
            "platforms":         ["twitter", "instagram"],
            "context":           {"release": "new EP"},
            "tone":              "authentic",
            "posts_per_platform": 2,
            "schedule_buffer":   False,
        })
    assert r.status_code == 200, r.text
    batch = r.json()
    assert batch["generated"] == 4
    assert len(batch["post_ids"]) == 4
    assert batch["scheduled_via_buffer"] == 0

    # ── Step 4: List posts — verify all are saved ─────────────────────────────
    r = client.get(f"/api/social/posts?artist_id={ARTIST_ID}")
    assert r.status_code == 200, r.text
    posts = r.json()["posts"]
    assert len(posts) >= 5  # 1 manual + 4 batch

    # ── Step 5: Filter by platform ────────────────────────────────────────────
    r = client.get(f"/api/social/posts?artist_id={ARTIST_ID}&platform=twitter")
    assert r.status_code == 200, r.text
    twitter_posts = r.json()["posts"]
    assert all(p["platform"] == "twitter" for p in twitter_posts)
    assert len(twitter_posts) >= 2  # at least the 2 batch twitter posts

    # ── Step 6: PATCH post to posted status ──────────────────────────────────
    r = client.patch(f"/api/social/posts/{manual_post_id}", json={
        "status":    "posted",
        "posted_at": "2026-05-15T18:05:00",
        "post_url":  "https://twitter.com/artisthandle/status/12345",
    })
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["status"] == "posted"

    # ── Step 7: Filter by status=posted ──────────────────────────────────────
    r = client.get(f"/api/social/posts?artist_id={ARTIST_ID}&status=posted")
    assert r.status_code == 200, r.text
    posted_posts = r.json()["posts"]
    assert any(p["id"] == manual_post_id for p in posted_posts)

    # ── Step 8: DELETE the manually created post ──────────────────────────────
    r = client.delete(f"/api/social/posts/{manual_post_id}")
    assert r.status_code == 204, r.text

    r = client.get(f"/api/social/posts/{manual_post_id}")
    assert r.status_code == 404
