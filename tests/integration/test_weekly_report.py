"""
IT.4b — Phase 3 Weekly Report Integration Test

Full flow (one test function, sequential assertions):
  1. Seed cross-phase data: pitches sent/replied, PR sent, booking sent, social posts
  2. Generate weekly report via POST /api/reports/weekly/generate (Claude Sonnet mocked)
  3. Assert report saved with correct structure (momentum_score, headline, insights)
  4. GET /api/reports/weekly/{report_id} — verify retrieval
  5. GET /api/reports/weekly?artist_id=... — verify list endpoint
"""

import json
import sqlite3
from unittest.mock import MagicMock, patch

import pytest


ARTIST_ID = "artist-report-001"
WEEK_START = "2026-05-04T00:00:00"
WEEK_END   = "2026-05-10T23:59:59"

_MOCK_REPORT_ANALYSIS = {
    "headline":        "Busy week — pitches sent, PR traction, social posts scheduled",
    "highlights":      [
        "3 pitches sent to curators",
        "1 PR reply received from Indie Pulse",
        "4 social posts scheduled",
    ],
    "insights":        (
        "The week demonstrated solid cross-platform activity. "
        "Curator outreach is building a pipeline. "
        "Social posting cadence is consistent and growing reach."
    ),
    "recommendations": "1. Follow up on open pitches day 3. 2. Engage with PR reply immediately.",
    "momentum_score":  7,
}


@pytest.fixture()
def client(tmp_path):
    from tests.integration.conftest import build_app, seed_artist
    from fastapi.testclient import TestClient
    db = str(tmp_path / "weekly_report.db")
    app = build_app(db)
    seed_artist(db, ARTIST_ID)
    with TestClient(app, raise_server_exceptions=True) as c:
        c._db = db
        yield c


def _seed_cross_phase_data(db_path: str):
    """Insert synthetic rows into all phase tables to give the report aggregator data."""
    conn = sqlite3.connect(db_path)

    # 3 pitches sent within the week
    for i in range(3):
        conn.execute(
            "INSERT OR IGNORE INTO pitches (id,artist_id,curator_id,status,subject,body,sent_at,created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (f"p-{i}", ARTIST_ID, f"cur-{i}", "sent",
             f"Pitch {i}", "Body", "2026-05-06T10:00:00", "2026-05-06T09:00:00"),
        )
    # 1 pitch replied
    conn.execute(
        "INSERT OR IGNORE INTO pitches (id,artist_id,curator_id,status,subject,body,replied_at,created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        ("p-replied", ARTIST_ID, "cur-x", "replied",
         "Pitch replied", "Body", "2026-05-07T12:00:00", "2026-05-05T09:00:00"),
    )

    # 2 PR outreach sent
    for i in range(2):
        conn.execute(
            "INSERT OR IGNORE INTO pr_outreach (id,artist_id,contact_id,status,subject,body,sent_at,created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (f"pr-{i}", ARTIST_ID, f"prc-{i}", "sent",
             f"PR {i}", "Body", "2026-05-07T11:00:00", "2026-05-07T10:00:00"),
        )

    # 1 booking inquiry sent
    conn.execute(
        "INSERT OR IGNORE INTO booking_inquiries (id,artist_id,contact_id,status,subject,body,sent_at,created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        ("bi-1", ARTIST_ID, "bc-1", "sent",
         "Booking inquiry", "Body", "2026-05-08T10:00:00", "2026-05-08T09:00:00"),
    )

    # 4 social posts in draft
    for i in range(4):
        conn.execute(
            "INSERT OR IGNORE INTO social_posts (id,artist_id,platform,content,status,created_at) "
            "VALUES (?,?,?,?,?,?)",
            (f"sp-{i}", ARTIST_ID, "twitter" if i % 2 == 0 else "instagram",
             f"Post content {i}", "draft", "2026-05-07T10:00:00"),
        )

    conn.commit()
    conn.close()


# ── Lifecycle test ────────────────────────────────────────────────────────────

def test_weekly_report_full(client):
    # Seed cross-phase data into the test DB
    _seed_cross_phase_data(client._db)

    # ── Step 1: Generate weekly report (Claude Sonnet mocked) ─────────────────
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=json.dumps(_MOCK_REPORT_ANALYSIS))]

    with patch("anthropic.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.return_value = mock_resp
        r = client.post("/api/reports/weekly/generate", json={
            "artist_id":  ARTIST_ID,
            "week_start": WEEK_START,
            "week_end":   WEEK_END,
        })
    assert r.status_code == 200, r.text
    report = r.json()

    # ── Step 2: Assert report structure ──────────────────────────────────────
    assert report["artist_id"] == ARTIST_ID
    assert report["momentum_score"] == 7
    assert len(report["headline"]) > 10
    assert len(report["insights"]) > 20
    assert "recommendations" in report
    assert report["week_start"] == WEEK_START
    assert report["week_end"] == WEEK_END
    report_id = report["id"]

    # ── Step 3: GET /api/reports/weekly/{report_id} ───────────────────────────
    # Note: momentum_score/headline/highlights are returned by the generate endpoint
    # but are NOT stored as DB columns (they live in the in-memory return dict only).
    # The GET endpoint returns only what's persisted: id, artist_id, week_start/end,
    # summary, insights, recommendations, generated_at.
    r = client.get(f"/api/reports/weekly/{report_id}")
    assert r.status_code == 200, r.text
    fetched = r.json()
    assert fetched["id"] == report_id
    assert fetched["artist_id"] == ARTIST_ID
    assert len(fetched.get("insights", "")) > 10

    # ── Step 4: LIST endpoint returns the report ──────────────────────────────
    r = client.get(f"/api/reports/weekly?artist_id={ARTIST_ID}")
    assert r.status_code == 200, r.text
    reports = r.json()["reports"]
    assert any(rpt["id"] == report_id for rpt in reports)

    # ── Step 5: Summary section reflects seeded data ──────────────────────────
    summary = report.get("summary", {})
    # Aggregator should have counted at least 3 sent pitches
    pitches_data = summary.get("pitches", {})
    assert pitches_data.get("sent", 0) >= 3
    # And at least 2 PR outreach
    pr_data = summary.get("pr_outreach", {})
    assert pr_data.get("sent", 0) >= 2

    # ── Step 6: 404 for unknown report ───────────────────────────────────────
    r = client.get("/api/reports/weekly/does-not-exist")
    assert r.status_code == 404
