"""R-33 — _anthropic_call_with_retry must be async and use asyncio.sleep.

Three tests:
  (a) Direct timing test: mock raises RateLimitError twice then succeeds.
      The total wall-clock time must be >= 1+2=3s (backoff sum for 2 retries).

  (b) Concurrency test: a fast asyncio.sleep(0.1) task runs alongside the
      retry helper. The fast task must complete DURING the helper's first
      1-second backoff window. If the helper still used time.sleep(), the
      fast task would block and complete only after the full retry sequence.

  (c) Verify the function signature is async (not sync) — importing the
      module and checking asyncio.iscoroutinefunction() is definitive.

Red: on main, _anthropic_call_with_retry is a sync def using time.sleep().
     (a) would pass trivially (time.sleep still elapses).
     (b) would FAIL — the fast task completes AFTER the helper (blocked).
     (c) would FAIL — asyncio.iscoroutinefunction() returns False.
"""
import asyncio
import time
import pytest
import anthropic
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# (c) Structural test: function must be a coroutine function
# ---------------------------------------------------------------------------

def test_r33_helper_is_coroutine_function():
    """_anthropic_call_with_retry must be declared 'async def', not 'def'."""
    import importlib
    import anthropic_utils
    importlib.reload(anthropic_utils)
    assert asyncio.iscoroutinefunction(anthropic_utils._anthropic_call_with_retry), (
        "_anthropic_call_with_retry must be an async function (R-33)"
    )


# ---------------------------------------------------------------------------
# (a) Timing test: retry backoff accumulates >= 1+2=3s for 2 RateLimitErrors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_r33_retry_backoff_is_non_blocking_asyncio_sleep(monkeypatch):
    """With 2 RateLimitErrors, total backoff must be >= 3s (1+2).

    Uses asyncio.sleep mock to avoid real wall-clock delay while still
    verifying the correct await calls are made with the right durations.
    """
    import importlib
    import anthropic_utils
    importlib.reload(anthropic_utils)

    sleep_calls = []

    async def fake_sleep(secs):
        sleep_calls.append(secs)

    monkeypatch.setattr(anthropic_utils.asyncio, "sleep", fake_sleep)

    call_count = 0
    def fake_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise anthropic.RateLimitError(
                "rate limit", response=MagicMock(status_code=429), body={}
            )
        r = MagicMock()
        r.content = [MagicMock(text="ok")]
        return r

    fake_client = MagicMock()
    fake_client.messages.create = fake_create

    result = await anthropic_utils._anthropic_call_with_retry(
        fake_client, model="haiku", messages=[]
    )

    assert call_count == 3, f"Expected 3 attempts (2 failures + 1 success), got {call_count}"
    assert sleep_calls == [1, 2], (
        f"Expected asyncio.sleep called with [1, 2], got {sleep_calls}"
    )
    assert result.content[0].text == "ok"


# ---------------------------------------------------------------------------
# (b) Concurrency test: event loop stays unblocked during retry backoff
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_r33_retry_does_not_block_event_loop():
    """A fast concurrent task must complete DURING the retry helper's backoff.

    If the helper uses time.sleep() (blocking), the fast task cannot run
    until the helper finishes. If the helper uses asyncio.sleep() (non-
    blocking), the fast task completes during the first 0.1s backoff window.

    We use a 0.1s backoff (not the real 1s) to keep the test fast, and a
    fast task that takes 0.05s. The fast task should complete before the
    helper finishes retrying.
    """
    import importlib
    import anthropic_utils
    importlib.reload(anthropic_utils)

    # Patch backoff to 0.1s so the test runs in < 0.5s
    monkeypatch = None  # using direct patch on module attribute
    original_backoff = anthropic_utils._BACKOFF_SECONDS
    anthropic_utils._BACKOFF_SECONDS = (0.1, 0.2, 0.4)
    anthropic_utils._MAX_ATTEMPTS    = 4

    fast_task_completed_at = []
    helper_completed_at    = []

    async def fast_task():
        await asyncio.sleep(0.05)
        fast_task_completed_at.append(time.monotonic())

    call_count = 0
    def fake_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise anthropic.RateLimitError(
                "rate limit", response=MagicMock(status_code=429), body={}
            )
        r = MagicMock()
        r.content = [MagicMock(text="done")]
        return r

    fake_client = MagicMock()
    fake_client.messages.create = fake_create

    async def run_helper():
        result = await anthropic_utils._anthropic_call_with_retry(
            fake_client, model="haiku", messages=[]
        )
        helper_completed_at.append(time.monotonic())
        return result

    # Run both concurrently
    await asyncio.gather(run_helper(), fast_task())

    assert fast_task_completed_at, "Fast task must have completed"
    assert helper_completed_at, "Helper must have completed"

    # The fast task (0.05s) must finish BEFORE the helper (0.1s backoff + retry)
    assert fast_task_completed_at[0] < helper_completed_at[0], (
        "Fast task must complete before the retry helper — "
        "if this fails, the helper is still using blocking time.sleep()"
    )

    # Restore
    anthropic_utils._BACKOFF_SECONDS = original_backoff
    anthropic_utils._MAX_ATTEMPTS    = len(original_backoff) + 1


# ---------------------------------------------------------------------------
# Non-retryable errors are re-raised immediately (no backoff)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_r33_non_retryable_error_raised_immediately(monkeypatch):
    """AuthenticationError must be raised immediately, no retry."""
    import importlib
    import anthropic_utils
    importlib.reload(anthropic_utils)

    sleep_calls = []

    async def fake_sleep(secs):
        sleep_calls.append(secs)

    monkeypatch.setattr(anthropic_utils.asyncio, "sleep", fake_sleep)

    def fake_create(**kwargs):
        raise anthropic.AuthenticationError(
            "bad key", response=MagicMock(status_code=401), body={}
        )

    fake_client = MagicMock()
    fake_client.messages.create = fake_create

    with pytest.raises(anthropic.AuthenticationError):
        await anthropic_utils._anthropic_call_with_retry(
            fake_client, model="haiku", messages=[]
        )

    assert sleep_calls == [], "No sleep must occur for non-retryable errors"
