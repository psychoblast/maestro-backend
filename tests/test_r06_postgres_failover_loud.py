"""
R-06 — Postgres init failure must fail loud.

Tests that when DATABASE_URL is set but Postgres init fails:
  - Default: sys.exit(1) — app refuses to start
  - DB_FAILOVER_TO_SQLITE=true: falls back to SQLite with a warning (no exit)
  - DATABASE_URL unset: SQLite, no message about Postgres

Run with: python3 -m pytest tests/test_r06_postgres_failover_loud.py -v
"""

import pytest


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))


def _failing_pg_init():
    raise Exception("Connection refused: no route to host")


def _ok_pg_init():
    pass  # succeeds silently


# ── _init_pg_connection exists (will AttributeError on unfixed code) ──────────

def test_function_exists():
    """_init_pg_connection helper must exist after the fix."""
    import main as m
    assert hasattr(m, "_init_pg_connection"), (
        "_init_pg_connection not found — apply the R-06 fix to main.py"
    )


# ── Postgres fails + no escape hatch → sys.exit(1) ───────────────────────────

def test_pg_fails_no_failover_exits(monkeypatch):
    """Postgres unreachable + DB_FAILOVER_TO_SQLITE unset → SystemExit(1)."""
    monkeypatch.setenv("DB_FAILOVER_TO_SQLITE", "")
    import main as m
    monkeypatch.setattr(m, "_pg_init", _failing_pg_init)

    with pytest.raises(SystemExit) as exc_info:
        m._init_pg_connection("postgresql://fake:5432/db")

    assert exc_info.value.code == 1


def test_pg_fails_false_failover_exits(monkeypatch):
    """DB_FAILOVER_TO_SQLITE=false also triggers exit (only 'true' enables fallback)."""
    monkeypatch.setenv("DB_FAILOVER_TO_SQLITE", "false")
    import main as m
    monkeypatch.setattr(m, "_pg_init", _failing_pg_init)

    with pytest.raises(SystemExit) as exc_info:
        m._init_pg_connection("postgresql://fake:5432/db")

    assert exc_info.value.code == 1


# ── Postgres fails + DB_FAILOVER_TO_SQLITE=true → SQLite fallback ────────────

def test_pg_fails_with_failover_returns_empty(monkeypatch, capsys):
    """Postgres fails + DB_FAILOVER_TO_SQLITE=true → returns '' (SQLite mode)."""
    monkeypatch.setenv("DB_FAILOVER_TO_SQLITE", "true")
    import main as m
    monkeypatch.setattr(m, "_pg_init", _failing_pg_init)

    result = m._init_pg_connection("postgresql://fake:5432/db")

    assert result == ""
    captured = capsys.readouterr()
    assert "WARNING" in captured.out or "fallback" in captured.out.lower() or "SQLite" in captured.out


# ── DATABASE_URL unset → SQLite, no exit ─────────────────────────────────────

def test_no_database_url_returns_empty(monkeypatch, capsys):
    """Empty database_url → returns '' immediately, no Postgres attempt."""
    import main as m

    result = m._init_pg_connection("")

    assert result == ""
    captured = capsys.readouterr()
    assert "PostgreSQL" not in captured.out


# ── Postgres succeeds → returns the original URL ─────────────────────────────

def test_pg_succeeds_returns_url(monkeypatch):
    """Postgres init succeeds → returns the passed-in database_url unchanged."""
    monkeypatch.setenv("DB_FAILOVER_TO_SQLITE", "")
    import main as m
    monkeypatch.setattr(m, "_pg_init", _ok_pg_init)

    result = m._init_pg_connection("postgresql://real:5432/db")

    assert result == "postgresql://real:5432/db"
