# PLMKR — Structured Logging Convention

**Last updated:** 2026-05-15  
**Applies to:** All Python service modules (`main.py`, `*_service.py`, `anthropic_utils.py`)

---

## Setup

`logging_config.py` initialises logging at app boot (`main.py:20`):

```python
from logging_config import setup_logging, get_logger
setup_logging()
log = get_logger("main")
```

Service modules use the standard stdlib logger at module level:

```python
import logging
log = logging.getLogger("pitch_service")
```

**Format:**
- When `RAILWAY_ENVIRONMENT` is set: JSON (one object per line) — machine-readable for log aggregators.
- Otherwise: human-readable `YYYY-MM-DDTHH:MM:SS LEVEL [name] event`.

---

## Convention

Every structured log call must pass `extra=` with at minimum an `event` key.

```python
log.info("event_name", extra={"event": "event_name", ...optional_fields...})
```

### Required fields

| Field | Type | Notes |
|-------|------|-------|
| `event` | `str` | Snake-case identifier. Matches the positional `msg` argument for easy grep. |

### Recommended fields

| Field | When to include |
|-------|-----------------|
| `artist_id` | Any log involving a specific artist |
| `duration_ms` | Any timed operation (API call, DB query, send) |
| `svc` | Service module name, when emitting from init/boot paths |
| `status` | Outcome of an operation: `"ok"`, `"skipped"`, `"retry"`, `"fail"` |
| `error` | `str(exception)` — only in WARNING/ERROR calls |

### Forbidden in extra

| Key | Reason |
|-----|--------|
| `module` | Reserved LogRecord attribute — raises `KeyError` at runtime |
| `message`, `asctime` | Reserved LogRecord attributes |
| Any credential or secret | Never log API keys, tokens, auth codes, or PII |

---

## Examples

### Service init (db_ready)

```python
log.info("db_ready", extra={"event": "db_ready", "svc": "pitch_service"})
```

### External API call (observability)

```python
log.info("anthropic_call", extra={
    "model":       "claude-haiku-4-5-20251001",
    "attempt":     1,
    "duration_ms": 342,
    "status":      "success",
})
```

### Scheduler sweep

```python
log.info("scheduler_poll_start", extra={
    "event":        "scheduler_poll_start",
    "artist_count": len(artists),
})
log.error("scheduler_poll_error", extra={
    "event":     "scheduler_poll_error",
    "artist_id": aid,
    "error":     str(e),
})
```

### Boot warnings (missing env vars)

```python
log.warning("boot_warning", extra={
    "event":  "boot_warning",
    "key":    "STRIPE_SECRET_KEY",
    "detail": "billing checkout disabled",
})
```

### Gmail send path

```python
log.info("email_sent", extra={
    "artist_id":   artist_id,
    "to":          to,
    "action":      "send",
    "result":      "ok",
    "latency_ms":  latency_ms,
})
```

---

## What NOT to log

- Prompt content, user messages, or email bodies (privacy + security)
- API key values, OAuth tokens, or any secrets
- Full stack traces in `extra=` — use `exc_info=True` on the log call instead
- Raw SQL queries with user-supplied values — log the operation name, not the query

---

## Observability endpoints

After boot, in-memory counters are available via admin endpoints (requires `X-API-Key`):

| Endpoint | What it shows |
|----------|---------------|
| `GET /api/admin/diagnostics/anthropic-stats` | Per-model call counts (total, success, retry, fail) |
| `GET /api/admin/diagnostics/gmail-stats` | Per-artist Gmail call counts |
| `GET /api/admin/diagnostics/performance` | Per-route p50/p95/p99 latency |
| `GET /api/admin/diagnostics` | Full snapshot: env vars SET/MISSING, service status, recent errors |

The ring buffer (last 200 ERROR entries) is accessible via `GET /api/admin/diagnostics` → `recent_errors`.

---

## Files touched in Unit 3 (May 15, 2026) logging audit

| File | Conversions |
|------|-------------|
| `release_service.py` | `init_release_db()` db_ready + stuck-action reset → structured |
| `pitch_service.py` | `init_pitch_db()` db_ready, Gmail token save/refresh, scheduler start/poll/error → structured |
| `booking_service.py` | `init_booking_db()` db_ready → structured |
| `pr_service.py` | `init_pr_db()` db_ready → structured |
| `social_service.py` | `init_social_db()` db_ready, report scheduler start/result/error → structured |
| `main.py` | Added `log = get_logger("main")`, boot warnings (ANTHROPIC/Twilio/Stripe), skills preload, TTS Kokoro/ElevenLabs → structured |

**Note:** Two `print()` calls preserved alongside `log.*` calls to satisfy existing `capsys`-based tests:
- `release_service.py:120` — `[Release] Reset N stuck...` (tested by `test_r07_broader_crash_recovery::test_stuck_row_reset_logged`)
- `main.py` — `[Kokoro] WARNING:...` (tested by `test_r19_kokoro_startup_warning::test_missing_files_prints_warning`)
