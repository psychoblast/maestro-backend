"""
R-21 — Migration failures must fail loud.

Tests that non-duplicate-column OperationalErrors in init_*_db() functions
raise RuntimeError (app refuses to start), while duplicate-column errors
are still swallowed silently (idempotent re-run behaviour preserved).

Run with: python3 -m pytest tests/test_r21_loud_migration_failures.py -v
"""

import importlib
import sqlite3
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_conn_raising_on(sql_fragment: str, error_msg: str = "database is locked"):
    """Return a MagicMock connection whose execute raises OperationalError on
    the given SQL fragment, and returns an empty fetchall for PRAGMA calls."""
    mock_conn = MagicMock()

    def fake_execute(sql, *args):
        if "PRAGMA table_info" in sql:
            result = MagicMock()
            result.fetchall.return_value = []
            return result
        if sql_fragment in sql:
            raise sqlite3.OperationalError(error_msg)
        return MagicMock()

    mock_conn.execute.side_effect = fake_execute
    return mock_conn


def _mock_conn_duplicate_column(sql_fragment: str):
    """Return a MagicMock connection whose execute raises 'duplicate column name'
    on the given fragment — simulates the idempotent case explicitly."""
    mock_conn = MagicMock()

    def fake_execute(sql, *args):
        if "PRAGMA table_info" in sql:
            result = MagicMock()
            result.fetchall.return_value = []  # guard passes, ALTER TABLE runs
            return result
        if sql_fragment in sql:
            raise sqlite3.OperationalError("duplicate column name: idempotency_key")
        return MagicMock()

    mock_conn.execute.side_effect = fake_execute
    return mock_conn


# ── pitch_service ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")


def test_pitch_migration_raises_on_non_duplicate_error():
    """Non-duplicate OperationalError during pitch migration must raise RuntimeError."""
    import pitch_service
    importlib.reload(pitch_service)

    mock_conn = _mock_conn_raising_on(
        "ALTER TABLE pitches ADD COLUMN idempotency_key",
        "database is locked",
    )
    with patch("sqlite3.connect", return_value=mock_conn):
        with pytest.raises(RuntimeError, match="Migration failure on table pitches"):
            pitch_service.init_pitch_db()


def test_pitch_migration_swallows_duplicate_column(tmp_path):
    """Duplicate-column OperationalError during pitch migration must be swallowed."""
    import pitch_service
    importlib.reload(pitch_service)

    mock_conn = _mock_conn_duplicate_column(
        "ALTER TABLE pitches ADD COLUMN idempotency_key",
    )
    with patch("sqlite3.connect", return_value=mock_conn):
        pitch_service.init_pitch_db()  # must not raise


def test_pitch_migration_idempotent(tmp_path, monkeypatch):
    """Calling init_pitch_db() twice on a real DB must not raise."""
    import pitch_service
    importlib.reload(pitch_service)
    pitch_service.init_pitch_db()
    pitch_service.init_pitch_db()  # second call — must not raise


# ── social_service ────────────────────────────────────────────────────────────

def test_social_migration_raises_on_non_duplicate_error():
    """Non-duplicate OperationalError during social migration must raise RuntimeError."""
    import social_service
    importlib.reload(social_service)

    mock_conn = _mock_conn_raising_on(
        "ALTER TABLE weekly_reports ADD COLUMN",
        "database is locked",
    )
    with patch("sqlite3.connect", return_value=mock_conn):
        with pytest.raises(RuntimeError, match="Migration failure on table weekly_reports"):
            social_service.init_social_db()


def test_social_migration_swallows_duplicate_column():
    """Duplicate-column OperationalError during social migration must be swallowed."""
    import social_service
    importlib.reload(social_service)

    mock_conn = _mock_conn_duplicate_column("ALTER TABLE weekly_reports ADD COLUMN")
    with patch("sqlite3.connect", return_value=mock_conn):
        social_service.init_social_db()  # must not raise


def test_social_migration_idempotent(tmp_path, monkeypatch):
    """Calling init_social_db() twice on a real DB must not raise."""
    import social_service
    importlib.reload(social_service)
    social_service.init_social_db()
    social_service.init_social_db()


# ── pr_service ────────────────────────────────────────────────────────────────

def test_pr_migration_raises_on_non_duplicate_error():
    """Non-duplicate OperationalError during PR migration must raise RuntimeError."""
    import pr_service
    importlib.reload(pr_service)

    mock_conn = _mock_conn_raising_on(
        "ALTER TABLE pr_outreach ADD COLUMN idempotency_key",
        "database is locked",
    )
    with patch("sqlite3.connect", return_value=mock_conn):
        with pytest.raises(RuntimeError, match="Migration failure on table pr_outreach"):
            pr_service.init_pr_db()


def test_pr_migration_swallows_duplicate_column():
    """Duplicate-column OperationalError during PR migration must be swallowed."""
    import pr_service
    importlib.reload(pr_service)

    mock_conn = _mock_conn_duplicate_column(
        "ALTER TABLE pr_outreach ADD COLUMN idempotency_key",
    )
    with patch("sqlite3.connect", return_value=mock_conn):
        pr_service.init_pr_db()  # must not raise


def test_pr_migration_idempotent(tmp_path, monkeypatch):
    """Calling init_pr_db() twice on a real DB must not raise."""
    import pr_service
    importlib.reload(pr_service)
    pr_service.init_pr_db()
    pr_service.init_pr_db()


# ── booking_service ───────────────────────────────────────────────────────────

def test_booking_migration_raises_on_non_duplicate_error():
    """Non-duplicate OperationalError during booking migration must raise RuntimeError."""
    import booking_service
    importlib.reload(booking_service)

    mock_conn = _mock_conn_raising_on(
        "ALTER TABLE booking_inquiries ADD COLUMN idempotency_key",
        "database is locked",
    )
    with patch("sqlite3.connect", return_value=mock_conn):
        with pytest.raises(RuntimeError, match="Migration failure on table booking_inquiries"):
            booking_service.init_booking_db()


def test_booking_migration_swallows_duplicate_column():
    """Duplicate-column OperationalError during booking migration must be swallowed."""
    import booking_service
    importlib.reload(booking_service)

    mock_conn = _mock_conn_duplicate_column(
        "ALTER TABLE booking_inquiries ADD COLUMN idempotency_key",
    )
    with patch("sqlite3.connect", return_value=mock_conn):
        booking_service.init_booking_db()  # must not raise


def test_booking_migration_idempotent(tmp_path, monkeypatch):
    """Calling init_booking_db() twice on a real DB must not raise."""
    import booking_service
    importlib.reload(booking_service)
    booking_service.init_booking_db()
    booking_service.init_booking_db()
