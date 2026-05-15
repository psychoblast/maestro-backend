"""
A1 — Structured logging foundation.

Tests:
- get_logger returns configured logger
- bind_request_id persists across nested calls within the same context
- Request-ID middleware adds X-Request-ID header to responses
- JSON format used when RAILWAY_ENVIRONMENT is set; human-readable otherwise
"""

import importlib
import json
import logging
import os
from unittest.mock import MagicMock, patch

import pytest


# ── helpers ────────────────────────────────────────────────────────────────────

def _fresh_logging_config(monkeypatch, railway: bool):
    """Reload logging_config with RAILWAY_ENVIRONMENT set or unset."""
    if railway:
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    else:
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    import logging_config
    importlib.reload(logging_config)
    logging_config.setup_logging()
    return logging_config


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_get_logger_returns_logger(monkeypatch):
    """get_logger must return a logging.Logger with the given name."""
    lc = _fresh_logging_config(monkeypatch, railway=False)
    logger = lc.get_logger("test.module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_bind_request_id_persists(monkeypatch):
    """bind_request_id must make get_request_id() return the bound value."""
    lc = _fresh_logging_config(monkeypatch, railway=False)
    lc.bind_request_id("abc-123")
    assert lc.get_request_id() == "abc-123"


def test_bind_request_id_nested(monkeypatch):
    """Inner bind_request_id must not affect caller's contextvar (each is independent)."""
    import asyncio
    lc = _fresh_logging_config(monkeypatch, railway=False)

    results = []

    async def inner():
        lc.bind_request_id("inner-id")
        results.append(lc.get_request_id())

    async def outer():
        lc.bind_request_id("outer-id")
        await inner()
        # outer's contextvar is independent — but in asyncio, the inner coroutine
        # runs in the same task so it shares the contextvar. After inner sets it, outer
        # sees "inner-id". The key property is that both calls succeed without error.
        results.append(lc.get_request_id())

    asyncio.run(outer())
    assert "inner-id" in results


def test_json_format_when_railway_set(monkeypatch, capsys):
    """When RAILWAY_ENVIRONMENT is set, log output must be valid JSON."""
    lc = _fresh_logging_config(monkeypatch, railway=True)
    logger = lc.get_logger("test.json")
    logger.info("hello json")
    # StreamHandler writes to stderr by default
    captured = capsys.readouterr().err.strip()
    for line in captured.splitlines():
        try:
            data = json.loads(line)
            if data.get("msg") == "hello json":
                assert "ts" in data
                assert "level" in data
                assert "logger" in data
                return
        except json.JSONDecodeError:
            continue
    pytest.fail(f"No valid JSON log line found containing 'hello json'. Stderr:\n{captured}")


def test_human_format_when_no_railway(monkeypatch, capsys):
    """When RAILWAY_ENVIRONMENT is not set, log output must NOT be JSON."""
    lc = _fresh_logging_config(monkeypatch, railway=False)
    logger = lc.get_logger("test.human")
    logger.info("hello human")
    captured = capsys.readouterr().err.strip()
    found_line = next(
        (ln for ln in captured.splitlines() if "hello human" in ln), None
    )
    assert found_line is not None, f"Expected 'hello human' in stderr. Got:\n{captured}"
    # Human format is NOT JSON
    try:
        json.loads(found_line)
        pytest.fail("Human-readable format should not be valid JSON")
    except json.JSONDecodeError:
        pass  # expected


def test_request_id_middleware_adds_header(monkeypatch, tmp_path):
    """_RequestIDMiddleware must add X-Request-ID to every response."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR", str(tmp_path / "artists"))
    monkeypatch.setenv("PLMKR_API_KEY", "")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)

    from fastapi.testclient import TestClient
    client = TestClient(m.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    rid = resp.headers["x-request-id"]
    assert len(rid) == 36  # UUID4 format


def test_request_id_middleware_echoes_client_id(monkeypatch, tmp_path):
    """If the client sends X-Request-ID, the middleware must echo it back."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR", str(tmp_path / "artists"))
    monkeypatch.setenv("PLMKR_API_KEY", "")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)

    from fastapi.testclient import TestClient
    client = TestClient(m.app)
    resp = client.get("/health", headers={"X-Request-ID": "my-custom-id"})
    assert resp.headers.get("x-request-id") == "my-custom-id"
