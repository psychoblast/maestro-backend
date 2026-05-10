"""
B-05 follow-up — STRIPE_DEV_ALLOW_UNSIGNED fails loud on Railway.

Railway sets RAILWAY_ENVIRONMENT automatically. If that env var is present
AND STRIPE_DEV_ALLOW_UNSIGNED=true, the app must refuse to start (sys.exit 1).

Run with:  python3 -m pytest tests/test_b05_stripe_dev_flag_prod_guard.py -v
"""

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest


def _load_app(monkeypatch, tmp_path, *, railway_env: str = "", dev_flag: str = ""):
    """Reload main.py with specified env. Returns (module, raised_exc_or_None)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-test")
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")

    if railway_env:
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", railway_env)
    else:
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    if dev_flag:
        monkeypatch.setenv("STRIPE_DEV_ALLOW_UNSIGNED", dev_flag)
    else:
        monkeypatch.delenv("STRIPE_DEV_ALLOW_UNSIGNED", raising=False)

    raised = None
    with patch("whisper.load_model", return_value=MagicMock()):
        try:
            import main as m
            importlib.reload(m)
        except SystemExit as exc:
            raised = exc
    return raised


def test_railway_plus_dev_flag_refuses_start(monkeypatch, tmp_path):
    """RAILWAY_ENVIRONMENT set + STRIPE_DEV_ALLOW_UNSIGNED=true → sys.exit(1)."""
    exc = _load_app(monkeypatch, tmp_path,
                    railway_env="production", dev_flag="true")
    assert exc is not None, (
        "Expected sys.exit(1) when RAILWAY_ENVIRONMENT is set and "
        "STRIPE_DEV_ALLOW_UNSIGNED=true. Add the startup guard to main.py."
    )
    assert exc.code == 1, f"Expected exit code 1, got {exc.code}"


def test_railway_staging_plus_dev_flag_refuses_start(monkeypatch, tmp_path):
    """Any RAILWAY_ENVIRONMENT value (not just 'production') triggers the guard."""
    exc = _load_app(monkeypatch, tmp_path,
                    railway_env="staging", dev_flag="true")
    assert exc is not None, (
        "Guard must fire for any non-empty RAILWAY_ENVIRONMENT, not just 'production'."
    )
    assert exc.code == 1


def test_no_railway_with_dev_flag_starts_ok(monkeypatch, tmp_path):
    """No RAILWAY_ENVIRONMENT + dev flag set → app boots (local dev mode)."""
    exc = _load_app(monkeypatch, tmp_path,
                    railway_env="", dev_flag="true")
    assert exc is None, (
        "App should boot when RAILWAY_ENVIRONMENT is unset, even with dev flag."
    )


def test_railway_without_dev_flag_starts_ok(monkeypatch, tmp_path):
    """RAILWAY_ENVIRONMENT set but dev flag not set → app boots normally."""
    exc = _load_app(monkeypatch, tmp_path,
                    railway_env="production", dev_flag="")
    assert exc is None, (
        "App should boot on Railway when STRIPE_DEV_ALLOW_UNSIGNED is not set."
    )


def test_neither_set_starts_ok(monkeypatch, tmp_path):
    """Neither Railway env nor dev flag → clean startup."""
    exc = _load_app(monkeypatch, tmp_path,
                    railway_env="", dev_flag="")
    assert exc is None
