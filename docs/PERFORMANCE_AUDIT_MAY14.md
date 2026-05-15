# PLMKR — Performance Audit, 2026-05-14

**Auditor:** Claude (autonomous Batch 3)
**Scope:** All Python source files in `~/maestro/`. Railway single-process container.
**Method:** Static analysis — hot loops, N+1 queries, sync I/O in async routes, unbounded accumulation.

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Low (applied) | 1 | Fixed in this commit |
| Medium (deferred) | 2 | PERF-MAY14 comment added |
| Low (noted, no action) | 3 | Acceptable at current scale |

---

## Findings

### APPLIED — pitch_service.py (inner list scan in inbox loop)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **File:line** | `pitch_service.py` (inbox scan loop, was ~line 1058) |
| **Pattern** | O(n) list comprehension inside a loop iterating up to 50 Gmail messages |
| **Impact** | For 50 inbox messages × 100 sent pitches = 5,000 inner iterations per scan |
| **Fix applied** | Pre-computed `curator_pitch_counts` dict before the loop (one pass over `pitches` instead of n passes) |

**Before:**
```python
sent_count = len([p for p in pitches if p["curator_id"] == pitch["curator_id"]])
```

**After:**
```python
# pre-computed before the loop
curator_pitch_counts: dict[str, int] = {cid: count, ...}
sent_count = curator_pitch_counts.get(pitch["curator_id"], 1)
```

---

### DEFERRED — pitch_service.py (Gmail N+1 API calls in inbox scan)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **File:line** | `pitch_service.py` — Gmail inbox scan loop, `messages().get(...).execute()` |
| **Pattern** | N individual Gmail API calls (up to 50) per inbox scan trigger |
| **Impact** | 50 round-trips × ~200ms each = ~10s per inbox scan. Acceptable at low frequency (every 6h), but blocks if scan frequency increases. |
| **Suggested fix** | Replace with `googleapiclient.http.BatchHttpRequest` to fetch all message details in one HTTP round-trip. Medium complexity — requires restructuring the loop to use callbacks. |
| **Deferred because** | Inbox scan runs every 6 hours via APScheduler. Not on the critical path for user-facing requests. |

---

### DEFERRED — social_service.py (sync httpx.post in async route)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **File:line** | `social_service.py:409` — `buffer_callback()` async route |
| **Pattern** | Blocking `httpx.post()` inside `async def buffer_callback()` |
| **Impact** | Blocks the uvicorn event loop for ~200–500ms during Buffer OAuth token exchange. Could cause latency spike if concurrent requests arrive at the same moment. |
| **Suggested fix** | Replace with `async with httpx.AsyncClient() as c: resp = await c.post(...)`. One-line change. |
| **Deferred because** | Buffer OAuth callback is a one-time flow per artist. Not a hot path. No concurrent users at current scale. |

---

### NOTED — SQLite connection per function call (all services)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Files** | `pitch_service.py`, `social_service.py`, `admin_service.py`, `pr_service.py`, `booking_service.py` |
| **Pattern** | New `sqlite3.connect(...)` on every function call (20+ call sites) |
| **Assessment** | Acceptable. SQLite connections are cheap (file-local, no network). Railway is single-process, single-thread async — no connection pool contention. At the current traffic level, this is not measurable overhead. |
| **No action** | Would require a thread-safe connection pool (e.g., `sqlite3.connect(check_same_thread=False)` with a `threading.local()` cache). Not worth the added complexity for this traffic level. |

---

### NOTED — _count_gmail_connected / _count_buffer_connected (admin health check)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **File:line** | `admin_service.py` — `_count_gmail_connected()` and `_count_buffer_connected()` |
| **Pattern** | Fetches all artist rows from SQLite and iterates in Python to count token presence |
| **Assessment** | O(n) per health check, but only 1–100 artists expected. Total cost < 1ms. Acceptable. |
| **No action** | Could be SQL `WHERE data LIKE '%access_token%'` but that's fragile on JSON blobs. Fine as-is. |

---

### NOTED — Anthropic/Gmail stats registry (unbounded growth)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Files** | `anthropic_utils.py`, `pitch_service.py` |
| **Pattern** | `_stats` / `_gmail_stats_registry` dicts grow one entry per unique model/artist_id seen |
| **Assessment** | PLMKR uses ~5 models and ~100 artists maximum. Total memory: negligible (< 1 KB). Bounded in practice by business domain. |
| **No action** | Not a concern at this scale. |

---

## New Performance Infrastructure (from this batch)

- `performance_metrics.py` — rolling per-route p50/p95/p99 (last 1000 samples)
- `/api/admin/diagnostics/performance` — live latency percentiles
- `_TimingMiddleware` — Server-Timing header on all responses
- Slow-request WARNING log at >2000ms with path/method/duration/status
