"""
Unit tests for B-07 — CORS origin lockdown.

Tests verify ALLOWED_ORIGINS env var drives the CORS allow-list,
and that the wildcard default is gone.
Run with:  python3 -m pytest tests/test_cors.py -v
"""

import importlib
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def _base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-test")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))


def _load_app(monkeypatch, allowed_origins: str = ""):
    if allowed_origins:
        monkeypatch.setenv("ALLOWED_ORIGINS", allowed_origins)
    else:
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return m


# ── Default origin list ───────────────────────────────────────────────────────

def test_default_origins_do_not_include_wildcard(_base_env, monkeypatch):
    m = _load_app(monkeypatch)
    assert "*" not in m.ALLOWED_ORIGINS


def test_default_origins_include_railway(_base_env, monkeypatch):
    m = _load_app(monkeypatch)
    assert any("railway.app" in o for o in m.ALLOWED_ORIGINS)


def test_default_origins_include_localhost(_base_env, monkeypatch):
    m = _load_app(monkeypatch)
    assert any("localhost" in o for o in m.ALLOWED_ORIGINS)


# ── Env override ──────────────────────────────────────────────────────────────

def test_env_override_replaces_defaults(_base_env, monkeypatch):
    m = _load_app(monkeypatch, "https://myapp.example.com,https://api.example.com")
    assert m.ALLOWED_ORIGINS == ["https://myapp.example.com", "https://api.example.com"]


def test_env_override_strips_whitespace(_base_env, monkeypatch):
    m = _load_app(monkeypatch, " https://a.com , https://b.com ")
    assert "https://a.com" in m.ALLOWED_ORIGINS
    assert "https://b.com" in m.ALLOWED_ORIGINS


def test_env_override_ignores_empty_segments(_base_env, monkeypatch):
    m = _load_app(monkeypatch, "https://a.com,,https://b.com,")
    assert "" not in m.ALLOWED_ORIGINS
    assert len(m.ALLOWED_ORIGINS) == 2


# ── CORS header behavior via TestClient ───────────────────────────────────────

def test_allowed_origin_gets_cors_header(_base_env, monkeypatch):
    m = _load_app(monkeypatch, "https://allowed.example.com")
    client = TestClient(m.app)
    resp = client.options(
        "/health",
        headers={
            "Origin": "https://allowed.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") == "https://allowed.example.com"


def test_disallowed_origin_no_cors_header(_base_env, monkeypatch):
    m = _load_app(monkeypatch, "https://allowed.example.com")
    client = TestClient(m.app)
    resp = client.options(
        "/health",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") != "https://evil.example.com"
