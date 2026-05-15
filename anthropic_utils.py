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

A5 observability: logs per-call metadata (model, tokens, attempt, duration_ms,
status). NEVER logs prompt content, messages, or response text.
"""

import asyncio
import time
import threading
import logging
import anthropic

log = logging.getLogger("anthropic_utils")

_RETRYABLE_ERRORS = (
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    anthropic.APITimeoutError,
)
_BACKOFF_SECONDS = (1, 2, 4)
_MAX_ATTEMPTS    = len(_BACKOFF_SECONDS) + 1  # 4 total: 1 original + 3 retries


# ── Per-model counters ────────────────────────────────────────────────────────

class _ModelStats:
    def __init__(self):
        self._lock   = threading.Lock()
        self.total   = 0
        self.success = 0
        self.retry   = 0
        self.fail    = 0

    def as_dict(self) -> dict:
        with self._lock:
            return {
                "total":   self.total,
                "success": self.success,
                "retry":   self.retry,
                "fail":    self.fail,
            }


_stats: dict[str, _ModelStats] = {}
_stats_lock = threading.Lock()


def _get_stats(model: str) -> _ModelStats:
    with _stats_lock:
        if model not in _stats:
            _stats[model] = _ModelStats()
        return _stats[model]


def get_anthropic_stats() -> dict:
    """Return per-model call counters. Safe to call at any time."""
    with _stats_lock:
        models = list(_stats.items())
    return {model: s.as_dict() for model, s in models}


# ── Retry wrapper with observability ─────────────────────────────────────────

async def _anthropic_call_with_retry(client: anthropic.Anthropic, **kwargs):
    """Async wrapper around client.messages.create() with exponential backoff retry.

    Returns the Message on success.
    Re-raises the last exception after all retries are exhausted.
    Non-retryable errors are raised immediately on the first attempt.

    Uses asyncio.sleep() between retries so the event loop remains responsive
    to other requests during the backoff window (R-33).

    A5: logs per-call metadata. Never logs prompt content or API keys.
    """
    model      = kwargs.get("model", "unknown")
    max_tokens = kwargs.get("max_tokens", None)
    s          = _get_stats(model)

    with s._lock:
        s.total += 1

    last_exc = None
    for attempt in range(_MAX_ATTEMPTS):
        t0 = time.perf_counter()
        try:
            result = client.messages.create(**kwargs)
            duration_ms = round((time.perf_counter() - t0) * 1000)
            with s._lock:
                s.success += 1
            log.info(
                "anthropic_call",
                extra={
                    "model":        model,
                    "max_tokens":   max_tokens,
                    "attempt":      attempt + 1,
                    "duration_ms":  duration_ms,
                    "status":       "success",
                },
            )
            return result
        except _RETRYABLE_ERRORS as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000)
            last_exc = exc
            with s._lock:
                s.retry += 1
            if attempt < len(_BACKOFF_SECONDS):
                sleep_secs = _BACKOFF_SECONDS[attempt]
                log.warning(
                    "anthropic_call",
                    extra={
                        "model":        model,
                        "max_tokens":   max_tokens,
                        "attempt":      attempt + 1,
                        "duration_ms":  duration_ms,
                        "status":       "retry",
                        "error":        type(exc).__name__,
                        "retry_in_s":   sleep_secs,
                    },
                )
                await asyncio.sleep(sleep_secs)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000)
            with s._lock:
                s.fail += 1
            log.error(
                "anthropic_call",
                extra={
                    "model":       model,
                    "max_tokens":  max_tokens,
                    "attempt":     attempt + 1,
                    "duration_ms": duration_ms,
                    "status":      "fail",
                    "error":       type(exc).__name__,
                },
            )
            raise

    with s._lock:
        s.fail += 1
    log.error(
        "anthropic_call",
        extra={
            "model":   model,
            "status":  "fail",
            "reason":  "retries_exhausted",
        },
    )
    raise last_exc
