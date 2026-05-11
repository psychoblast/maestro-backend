"""
Shared Anthropic API helpers for PLMKR services.

Provides _anthropic_call_with_retry() — a drop-in wrapper around
client.messages.create() that retries on transient errors (rate limits,
server errors, timeouts) with exponential backoff.

Retry policy:
  - Max 3 retries (4 total attempts)
  - Retries on: RateLimitError (429), InternalServerError (5xx), APITimeoutError
  - Does NOT retry: AuthenticationError, BadRequestError, or any other client error
  - Backoff: 1s → 2s → 4s between attempts

R-33 fix: uses asyncio.sleep() instead of time.sleep() so that retry backoff
does not block the FastAPI event loop during batch operations.
"""

import asyncio
import anthropic

_RETRYABLE_ERRORS = (
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.APITimeoutError,
)
_BACKOFF_SECONDS = (1, 2, 4)
_MAX_ATTEMPTS    = len(_BACKOFF_SECONDS) + 1  # 4 total: 1 original + 3 retries


async def _anthropic_call_with_retry(client: anthropic.Anthropic, **kwargs):
    """Async wrapper around client.messages.create() with exponential backoff retry.

    Returns the Message on success.
    Re-raises the last exception after all retries are exhausted.
    Non-retryable errors are raised immediately on the first attempt.

    Uses asyncio.sleep() between retries so the event loop remains responsive
    to other requests during the backoff window (R-33).
    """
    last_exc = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return client.messages.create(**kwargs)
        except _RETRYABLE_ERRORS as exc:
            last_exc = exc
            if attempt < len(_BACKOFF_SECONDS):
                sleep_secs = _BACKOFF_SECONDS[attempt]
                print(
                    f"[Anthropic] {type(exc).__name__} on attempt {attempt + 1}/{_MAX_ATTEMPTS}"
                    f" — retry in {sleep_secs}s"
                )
                await asyncio.sleep(sleep_secs)
    raise last_exc
