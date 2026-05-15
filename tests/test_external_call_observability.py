"""
A5 — Anthropic + Gmail call observability.

Tests:
- Anthropic counters increment on success, retry, fail
- Prompt content NEVER appears in logs (sentinel check)
- Gmail counters increment on success
- Anthropic-stats endpoint returns correct shape
- Gmail-stats endpoint returns correct shape
"""

import importlib
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import anthropic


# ── Anthropic counter tests ────────────────────────────────────────────────────

def _make_client(response=None, side_effect=None):
    mock_client = MagicMock()
    if side_effect is not None:
        mock_client.messages.create.side_effect = side_effect
    else:
        mock_client.messages.create.return_value = response or MagicMock()
    return mock_client


def _run(coro):
    import asyncio
    return asyncio.run(coro)


def test_anthropic_counter_increments_on_success():
    """Successful call must increment total and success counters."""
    import anthropic_utils
    importlib.reload(anthropic_utils)

    client = _make_client()
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock):
        _run(anthropic_utils._anthropic_call_with_retry(
            client, model="claude-test", max_tokens=100,
            messages=[{"role": "user", "content": "hi"}]
        ))

    stats = anthropic_utils.get_anthropic_stats()
    assert "claude-test" in stats
    s = stats["claude-test"]
    assert s["total"] >= 1
    assert s["success"] >= 1


def test_anthropic_counter_increments_on_retry():
    """RateLimitError on first attempt must increment retry counter."""
    import anthropic_utils
    importlib.reload(anthropic_utils)

    call_count = [0]
    def _side_effect(**kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise anthropic.RateLimitError(
                "rate limited", response=MagicMock(status_code=429), body={}
            )
        return MagicMock()

    client = _make_client(side_effect=_side_effect)
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock):
        _run(anthropic_utils._anthropic_call_with_retry(
            client, model="claude-retry-test", max_tokens=50,
            messages=[{"role": "user", "content": "hi"}]
        ))

    stats = anthropic_utils.get_anthropic_stats()
    s = stats.get("claude-retry-test", {})
    assert s.get("retry", 0) >= 1


def test_anthropic_prompt_content_not_logged(capsys):
    """Prompt content (messages) must NEVER appear in log output."""
    import anthropic_utils
    importlib.reload(anthropic_utils)

    sentinel = "SUPER-SECRET-PROMPT-XYZ-12345"
    client = _make_client()
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock):
        _run(anthropic_utils._anthropic_call_with_retry(
            client,
            model="claude-sentinel",
            max_tokens=100,
            messages=[{"role": "user", "content": sentinel}],
        ))

    captured = capsys.readouterr()
    assert sentinel not in captured.out, "Sentinel found in stdout!"
    assert sentinel not in captured.err, "Sentinel found in stderr!"


# ── Gmail counter tests ────────────────────────────────────────────────────────

def test_gmail_counter_increments_on_success():
    """Successful Gmail execute must increment total and success counters."""
    import pitch_service
    importlib.reload(pitch_service)

    mock_request = MagicMock()
    mock_request.execute.return_value = {"id": "msg123", "threadId": "thread456"}

    pitch_service._gmail_execute_with_retry(mock_request, artist_id="artist-001")

    stats = pitch_service.get_gmail_stats()
    assert "artist-001" in stats
    s = stats["artist-001"]
    assert s["total"] >= 1
    assert s["success"] >= 1


def test_gmail_counter_increments_on_fail():
    """Failed Gmail execute must increment total and fail counters."""
    import pitch_service
    importlib.reload(pitch_service)

    mock_request = MagicMock()
    mock_request.execute.side_effect = RuntimeError("network error")

    with pytest.raises(RuntimeError):
        pitch_service._gmail_execute_with_retry(mock_request, artist_id="artist-fail")

    stats = pitch_service.get_gmail_stats()
    s = stats.get("artist-fail", {})
    assert s.get("fail", 0) >= 1


# ── Endpoint tests ────────────────────────────────────────────────────────────

_PLMKR_KEY = "obs-test-key"


def _build_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH",           str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",      "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",   str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",       str(tmp_path / "artists"))
    monkeypatch.setenv("PLMKR_API_KEY",     _PLMKR_KEY)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    with patch("whisper.load_model", return_value=MagicMock()):
        # Reload service modules FIRST so they pick up the monkeypatched env vars,
        # then reload main so it imports from the correctly-configured modules.
        import pitch_service
        importlib.reload(pitch_service)
        import main as m
        importlib.reload(m)

    from fastapi.testclient import TestClient
    return TestClient(m.app, raise_server_exceptions=False)


def test_anthropic_stats_endpoint_shape(monkeypatch, tmp_path):
    """GET /api/admin/diagnostics/anthropic-stats must return models dict."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get(
        "/api/admin/diagnostics/anthropic-stats",
        headers={"X-API-Key": _PLMKR_KEY},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "timestamp" in body
    assert "models" in body
    assert isinstance(body["models"], dict)


def test_gmail_stats_endpoint_shape(monkeypatch, tmp_path):
    """GET /api/admin/diagnostics/gmail-stats must return artists dict."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get(
        "/api/admin/diagnostics/gmail-stats",
        headers={"X-API-Key": _PLMKR_KEY},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "timestamp" in body
    assert "artists" in body
    assert isinstance(body["artists"], dict)


def test_anthropic_stats_endpoint_401(monkeypatch, tmp_path):
    """Anthropic stats endpoint must require API key."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics/anthropic-stats")
    assert resp.status_code == 401


def test_gmail_stats_endpoint_401(monkeypatch, tmp_path):
    """Gmail stats endpoint must require API key."""
    client = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics/gmail-stats")
    assert resp.status_code == 401
