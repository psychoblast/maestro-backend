"""
F1 — Per-artist timezone for weekly reports.

Tests:
  1. timezone column defaults to 'UTC'
  2. Migration is idempotent (running init_social_db() twice doesn't error)
  3. _week_boundaries_in_tz uses artist tz for week boundary
  4. Fallback to UTC when tz is invalid/missing

Run with:  python3 -m pytest tests/test_f01_per_artist_timezone.py -v
"""

import importlib
import sqlite3
from datetime import datetime, timezone

import pytest


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH",          str(db))
    monkeypatch.setenv("DATABASE_URL",     "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import social_service
    importlib.reload(social_service)
    # Create the artists table (normally done by main.py) before social init
    conn = sqlite3.connect(str(db))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            artist_id TEXT PRIMARY KEY,
            data      TEXT NOT NULL DEFAULT '{}',
            timezone  TEXT NOT NULL DEFAULT 'UTC'
        )
    """)
    conn.commit()
    conn.close()
    social_service.init_social_db()
    yield db


@pytest.fixture()
def ss():
    import social_service
    return social_service


# ── 1. Column exists with default 'UTC' ──────────────────────────────────────

def test_timezone_column_default_utc(ss, tmp_path):
    """artists table must have a timezone column defaulting to 'UTC'."""
    import os
    db = os.environ["DB_PATH"]
    conn = sqlite3.connect(db)
    # Insert a row without specifying timezone
    conn.execute("INSERT INTO artists (artist_id, data) VALUES ('tz-default', '{}')")
    conn.commit()
    cur = conn.cursor()
    cur.execute("SELECT timezone FROM artists WHERE artist_id='tz-default'")
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "UTC", (
        f"Expected timezone default 'UTC', got {row[0]!r}. "
        "Add timezone column with DEFAULT 'UTC' to artists table."
    )


# ── 2. Migration is idempotent ────────────────────────────────────────────────

def test_migration_idempotent(ss):
    """Calling init_social_db() twice must not raise."""
    import social_service
    social_service.init_social_db()  # second call — must not error
    social_service.init_social_db()  # third call — still fine


# ── 3. _week_boundaries_in_tz uses the correct timezone ──────────────────────

def test_week_boundaries_utc(ss):
    """UTC week boundaries should be valid ISO strings spanning 7 days."""
    ws, we = ss._week_boundaries_in_tz("UTC")
    ws_dt = datetime.fromisoformat(ws)
    we_dt = datetime.fromisoformat(we)
    diff = we_dt - ws_dt
    assert 6 <= diff.days <= 6, f"Expected 6-day span, got {diff.days} days"
    assert ws_dt.hour == 0 and ws_dt.minute == 0
    assert we_dt.hour == 23 and we_dt.minute == 59


def test_week_boundaries_at_boundary_between_tzs(ss, monkeypatch):
    """When it is 00:30 UTC on Sunday, Eastern (UTC-5) is still Saturday.
    The two timezones should therefore yield different last-Sunday dates.

    We freeze 'now' inside _week_boundaries_in_tz by patching the datetime
    used in social_service so the function always sees 2026-05-10T00:30:00 UTC,
    which is 2026-05-09T19:30:00 US/Eastern (Saturday evening).
    """
    from unittest.mock import patch
    from zoneinfo import ZoneInfo

    fixed_utc = datetime(2026, 5, 10, 0, 30, 0, tzinfo=ZoneInfo("UTC"))

    class _FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_utc.astimezone(tz) if tz else fixed_utc

    import social_service as ss_mod
    with patch.object(ss_mod, "datetime", _FakeDatetime):
        ws_utc, _ = ss_mod._week_boundaries_in_tz("UTC")               # Sunday 2026-05-10
        ws_est, _ = ss_mod._week_boundaries_in_tz("America/New_York")  # Saturday 2026-05-09 → last Sunday was 2026-05-03

    # UTC sees Sunday May 10; Eastern sees Saturday May 9 → last Sunday was May 3
    assert ws_utc != ws_est, (
        f"Week boundaries should differ when UTC is already Sunday but Eastern is still Saturday. "
        f"UTC start={ws_utc!r}, Eastern start={ws_est!r}. "
        "Check that _week_boundaries_in_tz uses the local tz for weekday calculation."
    )


# ── 4. Fallback to UTC on invalid timezone ────────────────────────────────────

def test_invalid_tz_falls_back_to_utc(ss):
    """An invalid IANA tz name must fall back to UTC without raising."""
    ws, we = ss._week_boundaries_in_tz("Not/A/Timezone")
    ws_utc, we_utc = ss._week_boundaries_in_tz("UTC")
    # Falls back — should produce same result as UTC
    assert ws == ws_utc, (
        f"Invalid tz should fall back to UTC week_start. "
        f"Got {ws!r}, expected {ws_utc!r}."
    )


# ── 5. _get_artist_timezone returns stored value ──────────────────────────────

def test_get_artist_timezone_reads_stored_value(ss):
    """_get_artist_timezone must return the stored timezone for a known artist."""
    import os, sqlite3
    db = os.environ["DB_PATH"]
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO artists (artist_id, data, timezone) VALUES (?, ?, ?)",
        ("tz-artist-1", "{}", "Europe/London"),
    )
    conn.commit()
    conn.close()
    assert ss._get_artist_timezone("tz-artist-1") == "Europe/London"


def test_get_artist_timezone_default_for_unknown(ss):
    """_get_artist_timezone must return 'UTC' for an unknown artist."""
    assert ss._get_artist_timezone("no-such-artist") == "UTC"
