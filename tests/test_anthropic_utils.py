"""
Unit tests for anthropic_utils._anthropic_call_with_retry().

R-33 update: function is now async, uses asyncio.sleep instead of time.sleep.
All tests updated to use asyncio.run() and patch asyncio.sleep accordingly.

Verifies:
  - Success on first attempt returns result immediately
  - RateLimitError triggers retry with asyncio.sleep
  - InternalServerError triggers retry with asyncio.sleep
  - APITimeoutError triggers retry with asyncio.sleep
  - Non-retryable error (AuthenticationError) raised immediately
  - Three consecutive retries then success on 4th attempt (max retries used)
  - Four consecutive failures raises the last exception
  - asyncio.sleep() is called with correct backoff values (1, 2, 4)
"""

import asyncio
from unittest.mock import MagicMock, patch, call, AsyncMock

import pytest
import anthropic

from anthropic_utils import _anthropic_call_with_retry, _BACKOFF_SECONDS, _MAX_ATTEMPTS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_client(side_effects):
    """Build a mock client whose messages.create returns/raises side_effects in order."""
    client = MagicMock()
    client.messages.create.side_effect = side_effects
    return client


def _make_status_exc(cls, status=429):
    """Build an anthropic APIStatusError subclass with minimal httpx mocks."""
    mock_resp             = MagicMock()
    mock_resp.status_code = status
    mock_resp.headers     = {}
    mock_resp.text        = "error"
    return cls(message="err", response=mock_resp, body={})


def _make_timeout_exc():
    mock_req = MagicMock()
    return anthropic.APITimeoutError(request=mock_req)


def _run(coro):
    """Run a coroutine in a fresh event loop (matches codebase asyncio.run() pattern)."""
    return asyncio.run(coro)


FAKE_RESPONSE = MagicMock(name="AnthropicMessage")


# ── Tests: success path ───────────────────────────────────────────────────────

def test_success_on_first_attempt():
    client = _mock_client([FAKE_RESPONSE])
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = _run(_anthropic_call_with_retry(client, model="m", max_tokens=10, messages=[]))
    assert result is FAKE_RESPONSE
    client.messages.create.assert_called_once()
    mock_sleep.assert_not_called()


# ── Tests: retry on transient errors ─────────────────────────────────────────

@pytest.mark.parametrize("exc_factory", [
    lambda: _make_status_exc(anthropic.RateLimitError, 429),
    lambda: _make_status_exc(anthropic.InternalServerError, 503),
    lambda: _make_timeout_exc(),
], ids=["RateLimitError", "InternalServerError", "APITimeoutError"])
def test_retries_on_transient_error_then_succeeds(exc_factory):
    exc = exc_factory()
    client = _mock_client([exc, FAKE_RESPONSE])
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = _run(_anthropic_call_with_retry(client, model="m", max_tokens=10, messages=[]))

    assert result is FAKE_RESPONSE
    assert client.messages.create.call_count == 2
    mock_sleep.assert_called_once_with(_BACKOFF_SECONDS[0])


def test_uses_all_three_retries_then_succeeds():
    exc = _make_status_exc(anthropic.RateLimitError, 429)
    client = _mock_client([exc, exc, exc, FAKE_RESPONSE])
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = _run(_anthropic_call_with_retry(client, model="m", max_tokens=10, messages=[]))

    assert result is FAKE_RESPONSE
    assert client.messages.create.call_count == 4
    assert mock_sleep.call_args_list == [call(s) for s in _BACKOFF_SECONDS]


def test_raises_after_all_retries_exhausted():
    exc = _make_status_exc(anthropic.RateLimitError, 429)
    client = _mock_client([exc] * _MAX_ATTEMPTS)
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(anthropic.RateLimitError):
            _run(_anthropic_call_with_retry(client, model="m", max_tokens=10, messages=[]))

    assert client.messages.create.call_count == _MAX_ATTEMPTS


# ── Tests: non-retryable errors ───────────────────────────────────────────────

def test_auth_error_not_retried():
    exc = _make_status_exc(anthropic.AuthenticationError, 401)
    client = _mock_client([exc])
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(anthropic.AuthenticationError):
            _run(_anthropic_call_with_retry(client, model="m", max_tokens=10, messages=[]))

    client.messages.create.assert_called_once()
    mock_sleep.assert_not_called()


def test_bad_request_error_not_retried():
    exc = _make_status_exc(anthropic.BadRequestError, 400)
    client = _mock_client([exc])
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(anthropic.BadRequestError):
            _run(_anthropic_call_with_retry(client, model="m", max_tokens=10, messages=[]))

    client.messages.create.assert_called_once()
    mock_sleep.assert_not_called()


# ── Tests: kwargs passthrough ─────────────────────────────────────────────────

def test_kwargs_passed_through_to_create():
    client = _mock_client([FAKE_RESPONSE])
    kwargs = dict(model="claude-haiku-4-5-20251001", max_tokens=512,
                  system="sys", messages=[{"role": "user", "content": "hi"}],
                  extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"})
    with patch("anthropic_utils.asyncio.sleep", new_callable=AsyncMock):
        _run(_anthropic_call_with_retry(client, **kwargs))
    client.messages.create.assert_called_once_with(**kwargs)
