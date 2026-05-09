"""
Unit tests for social_service.py — no real credentials needed, all mocked.

Run with:  python3 -m pytest tests/ -v
"""

import json
import importlib
import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import social_service
    importlib.reload(social_service)
    social_service.init_social_db()
    yield db


@pytest.fixture()
def ss():
    import social_service
    return social_service


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_post(ss, post_id="post-001", platform="twitter", status="draft"):
    p = {
        "id":         post_id,
        "artist_id":  "artist-001",
        "platform":   platform,
        "content":    f"Test post for {platform}",
        "status":     status,
    }
    ss._db_create_post(p)
    return p


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_create_and_get_post(ss):
    _make_post(ss)
    p = ss._db_get_post("post-001")
    assert p["platform"] == "twitter"
    assert p["content"] == "Test post for twitter"
    assert p["engagement_stats"] == {}


def test_list_posts_filter_platform(ss):
    _make_post(ss, "tw-001", "twitter")
    _make_post(ss, "ig-001", "instagram")
    tweets = ss._db_list_posts("artist-001", platform="twitter")
    assert len(tweets) == 1
    assert tweets[0]["id"] == "tw-001"


def test_list_posts_filter_status(ss):
    _make_post(ss, "d-001", status="draft")
    _make_post(ss, "s-001", status="scheduled")
    scheduled = ss._db_list_posts("artist-001", status="scheduled")
    assert len(scheduled) == 1
    assert scheduled[0]["id"] == "s-001"


def test_update_post_status(ss):
    _make_post(ss)
    ss._db_update_post("post-001", {"status": "posted", "posted_at": "2026-05-09T18:00:00"})
    p = ss._db_get_post("post-001")
    assert p["status"] == "posted"
    assert "18:00:00" in p["posted_at"]


def test_update_post_engagement_stats(ss):
    _make_post(ss)
    ss._db_update_post("post-001", {"engagement_stats": {"likes": 42, "shares": 7}})
    p = ss._db_get_post("post-001")
    assert p["engagement_stats"]["likes"] == 42


def test_delete_post(ss):
    _make_post(ss)
    ss._db_delete_post("post-001")
    assert ss._db_get_post("post-001") == {}


def test_generate_social_post_returns_valid_shape(ss):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=(
        '{"content":"New single out now!","suggested_media_prompt":"Artist in studio",'
        '"optimal_posting_window":"Tuesday 7-9pm ET"}'
    ))]
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_anthropic.return_value.messages.create.return_value = mock_resp
        result = asyncio.run(ss.generate_social_post(
            {"artist_name": "Test Artist", "genre": "indie"},
            "twitter",
            {"release": "New single dropping Friday"},
        ))
    assert "content" in result
    assert "suggested_media_prompt" in result
    assert "optimal_posting_window" in result
    # Twitter limit enforced
    assert len(result["content"]) <= 280


def test_batch_posts_generates_correct_count(ss):
    mock_draft = {
        "content": "Test post content",
        "suggested_media_prompt": "Artist photo",
        "optimal_posting_window": "Monday 6pm",
    }
    with patch.object(ss, "_load_artist_data", return_value={"artist_name": "Test"}):
        with patch.object(ss, "generate_social_post", new=AsyncMock(return_value=mock_draft)):
            req = ss.BatchPostRequest(
                artist_id="artist-001",
                platforms=["twitter", "instagram"],
                posts_per_platform=2,
                schedule_buffer=False,
            )
            result = asyncio.run(ss.schedule_posts(req))
    assert result["generated"] == 4  # 2 platforms × 2 posts each
    assert result["scheduled_via_buffer"] == 0
