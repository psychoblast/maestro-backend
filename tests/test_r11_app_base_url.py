"""
R-11 — APP_BASE_URL defaults to local LAN IP in production.

Tests:
- Missing APP_BASE_URL in Railway env (RAILWAY_ENVIRONMENT set) → sys.exit(1)
- Missing APP_BASE_URL in local dev (RAILWAY_ENVIRONMENT unset) → falls back to localhost:8000 + WARNING
- Explicit APP_BASE_URL always used as-is in both environments
"""

import importlib
import logging
import sys
from unittest.mock import MagicMock, patch

import pytest


def _reload_main(monkeypatch, tmp_path):
    """Reload main with basic env setup, returning the module."""
    monkeypatch.setenv("DB_PATH",           str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",      "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",   str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",       str(tmp_path / "artists"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
    return m


def test_missing_app_base_url_on_railway_calls_sys_exit(monkeypatch, tmp_path):
    """APP_BASE_URL unset + RAILWAY_ENVIRONMENT set → sys.exit(1) at boot."""
    monkeypatch.delenv("APP_BASE_URL",        raising=False)
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

    with pytest.raises(SystemExit) as exc_info:
        _reload_main(monkeypatch, tmp_path)

    assert exc_info.value.code == 1


def test_missing_app_base_url_in_local_dev_falls_back_to_localhost(monkeypatch, tmp_path):
    """APP_BASE_URL unset + no RAILWAY_ENVIRONMENT → falls back to http://localhost:8000 + WARNING log."""
    monkeypatch.delenv("APP_BASE_URL",        raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    warning_calls = []

    def _capture_warning(msg, *args, **kwargs):
        extra = kwargs.get("extra", {})
        warning_calls.append(extra.get("key", msg))

    import logging_config
    import logging as _logging
    real_logger = _logging.getLogger("main")
    original_warning = real_logger.warning
    real_logger.warning = _capture_warning

    try:
        m = _reload_main(monkeypatch, tmp_path)
    finally:
        real_logger.warning = original_warning

    assert m.APP_BASE_URL == "http://localhost:8000"
    assert any("APP_BASE_URL" in str(k) for k in warning_calls), (
        f"Expected APP_BASE_URL boot_warning. Got warning_calls: {warning_calls}"
    )


def test_explicit_app_base_url_used_as_is_local(monkeypatch, tmp_path):
    """Explicit APP_BASE_URL is used unchanged in local dev."""
    monkeypatch.setenv("APP_BASE_URL",        "https://custom.example.com")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    m = _reload_main(monkeypatch, tmp_path)

    assert m.APP_BASE_URL == "https://custom.example.com"


def test_explicit_app_base_url_used_as_is_on_railway(monkeypatch, tmp_path):
    """Explicit APP_BASE_URL is used unchanged on Railway (no sys.exit)."""
    monkeypatch.setenv("APP_BASE_URL",        "https://maestro.up.railway.app")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

    m = _reload_main(monkeypatch, tmp_path)

    assert m.APP_BASE_URL == "https://maestro.up.railway.app"
