"""
R-02 — Startup writable-data check.

Tests that main.py's _check_data_writable() logs a loud warning when /data
is not writable, and is quiet when it is writable.

We exercise the function directly rather than reloading main.py (reloading
main.py triggers whisper/kokoro/scheduler init which is tested elsewhere and
is expensive). The function is a pure I/O side-effect test.

Run with:  python3 -m pytest tests/test_r02_data_writable_check.py -v
"""

import importlib
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Import the function under test ────────────────────────────────────────────

def _get_check_fn(monkeypatch, tmp_path):
    """Reload main.py with minimal env so _check_data_writable is importable."""
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-test")
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
    return m._check_data_writable


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_writable_dir_logs_ok(tmp_path, monkeypatch, capsys):
    """When DATA_DIR is writable, startup check prints success and no WARNING."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    fn = _get_check_fn(monkeypatch, tmp_path)

    fn()

    captured = capsys.readouterr()
    assert "writable" in captured.out.lower()
    assert "WARNING" not in captured.out


def test_unwritable_dir_logs_warning(tmp_path, monkeypatch, capsys):
    """When DATA_DIR is not writable, startup check prints a loud WARNING."""
    # Point DATA_DIR at a read-only directory
    ro_dir = tmp_path / "readonly"
    ro_dir.mkdir()
    ro_dir.chmod(0o555)

    monkeypatch.setenv("DATA_DIR", str(ro_dir))
    fn = _get_check_fn(monkeypatch, tmp_path)

    try:
        fn()
        captured = capsys.readouterr()
        assert "WARNING" in captured.out, (
            "Expected loud WARNING when DATA_DIR is not writable. "
            "Add _check_data_writable() to main.py startup."
        )
        assert "volume" in captured.out.lower() or "writable" in captured.out.lower()
    finally:
        ro_dir.chmod(0o755)  # restore so tmp_path cleanup works


def test_missing_dir_triggers_warning(tmp_path, monkeypatch, capsys):
    """A DATA_DIR path that can't be created (parent is read-only) triggers WARNING."""
    ro_parent = tmp_path / "readonly_parent"
    ro_parent.mkdir()
    ro_parent.chmod(0o555)
    missing = ro_parent / "data"

    monkeypatch.setenv("DATA_DIR", str(missing))
    fn = _get_check_fn(monkeypatch, tmp_path)

    try:
        fn()
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
    finally:
        ro_parent.chmod(0o755)
