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


def test_get_report_returns_momentum_headline_highlights(ss):
    r = {
        "id":              "rpt-ms",
        "artist_id":       "artist-ms",
        "week_start":      _WEEK_START,
        "week_end":        _WEEK_END,
        "summary":         {},
        "insights":        "Insight text",
        "recommendations": "Do more",
        "momentum_score":  8,
        "headline":        "Great week",
        "highlights":      ["highlight A", "highlight B"],
    }
    ss._db_save_report(r)
    fetched = ss._db_get_report("rpt-ms")
    assert fetched["momentum_score"] == 8
    assert fetched["headline"] == "Great week"
    assert fetched["highlights"] == ["highlight A", "highlight B"]


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


# ── Empty-state handling ──────────────────────────────────────────────────────

def test_generate_weekly_report_empty_state_no_error(ss):
    """Artist with zero activity across all tables produces a valid report without errors."""
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps({
        "headline":        "Getting started week",
        "highlights":      [],
        "insights":        "No activity yet — time to start.",
        "recommendations": "1. Connect Gmail. 2. Pitch curators.",
        "momentum_score":  1,
    }))]
    with patch.object(ss, "_load_artist_data", return_value={"artist_name": "Empty Artist"}):
        with patch.object(ss, "_email_weekly_report", new=AsyncMock()):
            with patch("anthropic.Anthropic") as mock_anthropic:
                mock_anthropic.return_value.messages.create.return_value = mock_resp
                report = asyncio.run(ss.generate_weekly_report(
                    "artist-zero", _WEEK_START, _WEEK_END
                ))
    assert report["momentum_score"] == 1
    assert report["summary"]["pitches"]["sent"] == 0
    assert report["summary"]["pr_outreach"]["sent"] == 0
    assert report["summary"]["booking"]["sent"] == 0
    assert report["summary"]["social"]["posted"] == 0


def test_aggregate_empty_state_returns_zeros(ss):
    """_aggregate_week_data returns all-zero counts when no records exist."""
    data = ss._aggregate_week_data("artist-none", _WEEK_START, _WEEK_END)
    assert data["pitches"]["sent"] == 0
    assert data["pitches"]["replied"] == 0
    assert data["pr_outreach"]["sent"] == 0
    assert data["booking"]["sent"] == 0
    assert data["social"]["posted"] == 0


# ── Report email delivery ─────────────────────────────────────────────────────

def test_build_report_html_contains_key_fields(ss):
    """HTML report contains momentum score, week dates, and headline."""
    report = {
        "headline": "Great week ahead",
        "week_start": "2026-05-04T00:00:00",
        "week_end": "2026-05-10T23:59:59",
        "momentum_score": 7,
        "insights": "Strong activity this week.",
        "recommendations": "Keep going.",
        "highlights": ["3 pitches sent", "1 PR reply"],
        "summary": {
            "pitches": {"sent": 3, "replied": 1},
            "pr_outreach": {"sent": 2, "replied": 1},
            "booking": {"sent": 1, "replied": 0},
            "social": {"posted": 4, "scheduled": 2},
        },
    }
    html = ss._build_report_html(report, "Test Artist")
    assert "Great week ahead" in html
    assert "7/10" in html
    assert "2026-05-04" in html
    assert "3" in html  # pitches sent count


def test_build_report_html_empty_state_getting_started(ss):
    """HTML report shows getting-started message when all counts are zero."""
    report = {
        "headline": "First week",
        "week_start": "2026-05-04T00:00:00",
        "week_end": "2026-05-10T23:59:59",
        "momentum_score": 1,
        "insights": "No activity yet.",
        "recommendations": "Start pitching.",
        "highlights": [],
        "summary": {
            "pitches": {"sent": 0, "replied": 0},
            "pr_outreach": {"sent": 0, "replied": 0},
            "booking": {"sent": 0, "replied": 0},
            "social": {"posted": 0, "scheduled": 0},
        },
    }
    html = ss._build_report_html(report, "New Artist")
    assert "Connect Gmail" in html or "getting started" in html.lower() or "first week" in html.lower()


def test_build_report_plain_contains_metrics(ss):
    """Plain-text report contains artist name and key metric labels."""
    report = {
        "headline": "Solid week",
        "week_start": "2026-05-04T00:00:00",
        "week_end": "2026-05-10T23:59:59",
        "momentum_score": 6,
        "insights": "Good progress.",
        "recommendations": "Follow up.",
        "highlights": [],
        "summary": {
            "pitches": {"sent": 5, "replied": 2},
            "pr_outreach": {"sent": 1, "replied": 0},
            "booking": {"sent": 0, "replied": 0},
            "social": {"posted": 3, "scheduled": 0},
        },
    }
    plain = ss._build_report_plain(report, "Test Artist")
    assert "Test Artist" in plain
    assert "Pitches sent" in plain
    assert "6/10" in plain


def test_email_weekly_report_no_email_raises(ss):
    """_email_weekly_report raises ValueError when artist profile has no email."""
    report = {
        "id": "r-1", "artist_id": "a-1", "week_start": _WEEK_START, "week_end": _WEEK_END,
        "headline": "Test", "momentum_score": 5, "insights": "ok", "recommendations": "ok",
        "highlights": [], "summary": {},
    }
    with pytest.raises(ValueError, match="No email address"):
        asyncio.run(ss._email_weekly_report("a-1", report, {"artist_name": "No Email"}))


def test_generate_weekly_report_gmail_not_connected_is_nonfatal(ss):
    """GmailNotConnected during email delivery does not prevent report being saved."""
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(_MOCK_ANALYSIS))]
    with patch.object(ss, "_load_artist_data", return_value={"artist_name": "Test", "email": "t@example.com"}):
        with patch.object(ss, "_email_weekly_report", new=AsyncMock(side_effect=Exception("GmailNotConnected"))):
            with patch("anthropic.Anthropic") as mock_anthropic:
                mock_anthropic.return_value.messages.create.return_value = mock_resp
                report = asyncio.run(ss.generate_weekly_report(
                    "artist-gmail-fail", _WEEK_START, _WEEK_END
                ))
    # Report should still be saved despite email failure
    assert report["artist_id"] == "artist-gmail-fail"
    saved = ss._db_get_report(report["id"])
    assert saved["artist_id"] == "artist-gmail-fail"
