"""
Unit tests for social_service.py weekly report functions.

Run with:  python3 -m pytest tests/ -v
"""

import json
import importlib
import asyncio
import sqlite3
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

_WEEK_START = "2026-05-04T00:00:00"
_WEEK_END   = "2026-05-10T23:59:59"

_MOCK_ANALYSIS = {
    "headline":        "Steady week with promising PR traction",
    "highlights":      ["3 pitches sent", "1 PR reply received", "2 posts published"],
    "insights":        "The week showed solid fundamentals. Curator pitch response rate is improving.",
    "recommendations": "1. Follow up on PR reply. 2. Schedule next batch of social posts.",
    "momentum_score":  6,
}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_save_and_get_report(ss):
    r = {
        "id":              "rpt-001",
        "artist_id":       "artist-001",
        "week_start":      _WEEK_START,
        "week_end":        _WEEK_END,
        "summary":         {"pitches": {"sent": 3}},
        "insights":        "Test insight",
        "recommendations": "Test recommendation",
    }
    ss._db_save_report(r)
    fetched = ss._db_get_report("rpt-001")
    assert fetched["artist_id"] == "artist-001"
    assert fetched["summary"]["pitches"]["sent"] == 3


def test_list_reports_for_artist(ss):
    for i in range(3):
        ss._db_save_report({
            "id":         f"rpt-{i}",
            "artist_id":  "artist-list",
            "week_start": f"2026-04-{14+i*7:02d}T00:00:00",
            "week_end":   f"2026-04-{20+i*7:02d}T23:59:59",
            "summary":    {}, "insights": "", "recommendations": "",
        })
    reports = ss._db_list_reports("artist-list")
    assert len(reports) == 3


def test_aggregate_week_data_returns_structure(ss):
    data = ss._aggregate_week_data("artist-nodata", _WEEK_START, _WEEK_END)
    assert "pitches" in data
    assert "pr_outreach" in data
    assert "booking" in data
    assert "social" in data
    assert data["pitches"]["sent"] == 0


def test_aggregate_counts_social_posts(ss):
    # Manually insert a posted social post within the week
    conn = sqlite3.connect(str(ss._DB_PATH))
    conn.execute(
        "INSERT INTO social_posts (id,artist_id,platform,content,status,created_at) "
        "VALUES (?,?,?,?,?,?)",
        ("sp-1", "artist-001", "twitter", "test", "posted", "2026-05-07T10:00:00"),
    )
    conn.commit()
    conn.close()
    data = ss._aggregate_week_data("artist-001", _WEEK_START, _WEEK_END)
    assert data["social"]["posted"] == 1


def test_generate_weekly_report_saves_to_db(ss):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(_MOCK_ANALYSIS))]
    with patch.object(ss, "_load_artist_data", return_value={"artist_name": "Test"}):
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = mock_resp
            report = asyncio.run(ss.generate_weekly_report(
                "artist-001", _WEEK_START, _WEEK_END
            ))
    assert report["momentum_score"] == 6
    assert len(report["insights"]) > 10
    # Verify saved to DB
    saved = ss._db_get_report(report["id"])
    assert saved["artist_id"] == "artist-001"


def test_generate_weekly_report_defaults_to_last_week(ss):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(_MOCK_ANALYSIS))]
    with patch.object(ss, "_load_artist_data", return_value={"artist_name": "Test"}):
        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_anthropic.return_value.messages.create.return_value = mock_resp
            # No week_start/week_end — should default without raising
            report = asyncio.run(ss.generate_weekly_report("artist-001"))
    assert "week_start" in report
    assert "week_end" in report
    assert report["artist_id"] == "artist-001"
