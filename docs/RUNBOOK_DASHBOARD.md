# PLMKR Admin Dashboard — Operational Runbook

Symptom → diagnosis → action. Each section is 3-5 sentences. Keep this doc open while triaging.

---

## First-time setup

**URL (Railway):** `https://<your-app>.railway.app/admin/dashboard`

Navigate to the URL in any browser. The HTML shell loads without authentication. A key-prompt
modal appears — enter the value of `PLMKR_API_KEY` from your Railway Variables dashboard. The key
is stored in `sessionStorage` for this tab only (cleared on tab close). If you don't have the key,
retrieve it from Railway → Your Service → Variables → `PLMKR_API_KEY`. Do not share it; it
authenticates all admin and data-mutation endpoints.

---

## Symptom: Recent Errors section is showing entries

**Diagnosis.** The ring buffer (`logging_config.py`) holds the last 200 error/warning log entries.
Entries appear here when any Python logger calls `.error()` or `.warning()` anywhere in the app —
scheduler misfires, Anthropic retry exhaustion, Gmail send failures, and DB errors all land here.

**Action.**
1. Click any error row to copy the full JSON entry to clipboard; paste into your chat session or
   a search to identify the source logger (`svc` field) and event name (`event` field).
2. If `svc: pitch_service` and `event: gmail_send_fail` — check R-16 (Gmail OAuth env vars) and
   the Gmail Stats section for failure counts.
3. If `svc: anthropic_utils` and `event: anthropic_retry_exhausted` — check the Anthropic Usage
   section for high fail counts; this usually means rate-limit pressure or a bad prompt.
4. A single isolated error is usually safe to ignore. Repeated errors (same event every 30 s)
   indicate a persistent fault — look at the scheduler queue and deep health first.
5. Escalate if: `db_connected` is false in Deep Health, or errors are arriving faster than the
   30-second refresh can clear them.

---

## Symptom: Deep Health is RED (returns 503)

**Diagnosis.** The `/api/admin/health/deep` endpoint returns 503 when `db_connected=False`
(Railway uses this to trigger a service restart). Other fields — scheduler, disk, Gmail tokens —
are informational and do not affect the status code.

**Action.**
1. Confirm `db_connected: false` in the raw JSON (click `{ }` in the Deep Health section).
2. If `DATABASE_URL` is set: check Railway → Your Database → Status. If the Postgres service is
   down or the volume is full, Railway will restart it automatically — wait 60 s and refresh.
3. If using SQLite (`DB_PATH=/data/memory.db`): check `volume.writable` in the Diagnostics
   section. If false, the `/data` volume is not mounted — see R-02 (Railway volume creation).
4. If `scheduler_running: false` is the only anomaly (not DB): the scheduler was never enabled.
   Set `SCHEDULER_ENABLED=dry_run` in Railway Variables to start it (see SCHEDULER_AUDIT.md).
5. If the service restarted but health is still 503 after 2 minutes, check Railway build logs
   for boot errors — `APP_BASE_URL` not set on Railway is the most common crash cause (R-11).

---

## Symptom: Performance section shows a route with p95 > 2 s

**Diagnosis.** The rolling 1 000-request p95 window is recorded by `_TimingMiddleware`
(`performance_metrics.py`). Latency above 2 s on most routes indicates either Anthropic API
latency, a slow DB query, or a Railway cold start.

**Action.**
1. Identify the slow route. If it is `/api/pitches/generate`, `/api/pr/generate`, or any
   route that calls Claude — check the Anthropic Stats section. High retry or fail counts mean
   rate-limit pressure is adding backoff delay (R-13 fix: exponential retry with `asyncio.sleep`).
2. If the slow route is a DB-read route (`/api/artist`, `/api/pitches/*`) — check
   `volume.free_mb` in Diagnostics. SQLite on a near-full volume degrades dramatically.
3. Cold starts on Railway (new deploy or service restart) inflate p99 because the first request
   warms up Kokoro TTS. This is expected; p95 normalises after ~5 minutes of traffic.
4. Click `{ }` on the Performance section to see raw percentile data — compare p50 vs p99 to
   distinguish consistent slowness (p50 high) from tail-latency spikes (p99 high, p50 normal).

---

## Symptom: Anthropic Stats showing unexpectedly high call counts

**Diagnosis.** Counters accumulate since process start (they are in-memory, not persisted). A
sudden spike in `total` or `retry` usually means the scheduler fired a bulk action, a retry loop
misfired, or the pitch-batch endpoint was called in a tight loop by a client.

**Action.**
1. Compare `total` vs `success` vs `retry`. High `retry` with low `fail` means rate-limit
   pressure is being handled correctly. High `fail` means requests are failing after exhausting
   retries — check the Recent Errors section for `anthropic_retry_exhausted` events.
2. Check the Scheduler Queue section — if `last_completed` shows many actions executed in a short
   window, the scheduler processed a backlog (expected on first enable of `SCHEDULER_ENABLED=true`).
3. If no scheduler activity is visible but counts are high, a client is calling generation
   endpoints in a loop. Check Railway request logs for repeated calls to `/api/pitches/generate`.
4. `total` resets to 0 on service restart — if the number looks impossibly large for your usage,
   confirm uptime in Railway before escalating.

---

## Symptom: Gmail Stats showing zero calls for an artist that should be active

**Diagnosis.** Gmail call counters accumulate since process start. Zero calls for an active artist
means either the scheduler has not fired for that artist, OAuth has expired, or the scheduler is
still in `dry_run` mode (which does not actually send email).

**Action.**
1. Check `SCHEDULER_ENABLED` in the Diagnostics environment snapshot. If it shows `MISSING` or
   `false`, no jobs will fire — set `SCHEDULER_ENABLED=dry_run` first to observe, then `true`
   to send real email (see SCHEDULER_AUDIT.md).
2. If `SCHEDULER_ENABLED=true` but counts are still zero — check the Scheduler Queue section.
   If `running: false` appears in the Diagnostics scheduler block, the APScheduler instance died.
   A service restart will reinitialise it.
3. If the scheduler is running and `dry_run` is off, zero Gmail calls means the artist has no
   pending `campaign_actions` in the DB (Scheduler Queue → Next Pending should confirm this).
4. OAuth expiry does not prevent scheduler job execution — it causes a `gmail_send_fail` error
   in Recent Errors. Look for that event if the job fires but nothing sends.

---

## Symptom: Scheduler shows jobs queued but none completing

**Diagnosis.** The Scheduler Queue section shows `next_pending` entries accumulating but
`last_completed` stays empty or stale. This means the APScheduler `_execute_campaign_actions`
job is either not running, aborting silently, or in `dry_run` mode.

**Action.**
1. Check `SCHEDULER_ENABLED` in Diagnostics. If it is `dry_run`, actions are intentionally
   not executed — they log `would_have_fired` only. Set to `true` when ready to go live.
2. Check the Recent Errors section for `campaign_executor_error` events. These appear when
   `execute_all_due_campaign_actions()` raises an uncaught exception — often a DB lock or a
   missing env var for a downstream service (Gmail, Buffer).
3. Check `scheduler_running` in Deep Health raw JSON. If `false`, the scheduler crashed.
   A Railway redeploy reinitialises it; the `_SCHEDULER_ENABLED` guard prevents double-start
   (R-30 fix).
4. If `running: true` and `SCHEDULER_ENABLED=true` but actions stay pending: check
   `scheduled_for` timestamps. Actions with a future timestamp are correctly queued — they will
   fire at their scheduled time, not immediately.

---

## Symptom: Dashboard won't load at all

**Diagnosis.** The `/admin/dashboard` route is unauthenticated (R-35 fix), so a 4xx/5xx on
page load means the Railway service itself is down, not an auth issue.

**Action.**
1. Check `https://<your-app>.railway.app/health` — if that also fails, the service is not
   running. Go to Railway → Your Service → Deployments and check the latest deployment status.
2. If the latest deployment shows "Failed": check build logs. Common causes: `APP_BASE_URL` not
   set (R-11 — `sys.exit(1)` at boot), `STRIPE_DEV_ALLOW_UNSIGNED=true` in production (hard-fail
   guard), or a pip install failure.
3. If the deployment shows "Active" but the URL is unreachable: check Railway networking
   (custom domain DNS propagation, or Railway's own status page at status.railway.app).
4. If the page loads but sections show "Error loading: Unauthorized": your stored
   `sessionStorage` key is wrong or expired — click Sign Out on the header to clear it and
   re-enter the key. (The sign-out button remains visible even when data fails.)
5. If only one section fails and others load: that specific endpoint has a bug — check Recent
   Errors for the relevant service name and open a bug against the failing route.
