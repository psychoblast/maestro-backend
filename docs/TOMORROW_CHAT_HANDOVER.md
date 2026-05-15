# PLMKR — Tomorrow Chat Handover Prompt

**This file is a ready-to-paste prompt for a fresh Claude Code chat.**
**Copy everything from the "BEGIN PASTE" marker below into the new chat.**

---

---BEGIN PASTE---

## Who I am and what PLMKR is

I'm Tommy Lam (handle: psychoblast), non-technical founder working through Claude Code on Ubuntu 24.04 running on a Mac Mini. I run several ventures — for this session we are working exclusively on **PLMKR**, owned by **Marquis Holdings LLC (New Mexico)**. Do not conflate with Mind Vision LLC (Wyoming) or RÊVE MUSIC GROUP INC. (Canada) — these are separate entities.

PLMKR is a release-engineering SaaS platform for independent artists. The backend automates: pitch emails to playlist curators, PR outreach, booking inquiries, social post scheduling, and weekly AI-generated reports. Agents take real-world actions — they don't just give advice.

## Repo locations and identities

- **Backend:** `~/maestro/` — this is the only repo for this session
- **GitHub:** `psychoblast/maestro-backend` (SSH via host alias `github-psychoblast`, port 443 on `ssh.github.com` — port 22 is blocked on my network; do NOT change this)
- **Frontend:** `~/Desktop/ReveNation/` — **OFF LIMITS** for any PLMKR session. Different product (RÊVE NATION), different entity (Mind Vision LLC), different repo.
- **Git author:** Tommy Lam `<mypsychoblast@gmail.com>` (placeholder; swap to Marquis-aligned email when that exists)

## Current state at end of May 15, 2026

- **main HEAD:** `a996082`
- **Tag:** `v0.1-eod-2026-05-15-s2` → `a996082`
- **Test suite:** 296/296 GREEN (`python3 -m pytest -q` → 296 passed ~145s)
- **Risk register:** All 34 code-side risks accounted for. 28 fully mitigated, 1 partially mitigated (R-30 Option B), 5 open (all Tommy/Railway-gated — no code blockers remaining). R-26, R-27 accepted deferrals; R-31 code-side open (low priority, product decision needed).
- **Deploy status:** Local dev fully functional. Railway deploy BLOCKED — Railway trial expired May 14. Need $5/mo Hobby plan to create persistent volume (R-02). All code is ready to deploy once Railway billing is sorted.

## What was accomplished May 15 (two sessions)

### Session 1 — Hardening and observability (4 units)

**Unit 1** — R-20 healthcheckPath verification: `railway.json` already had `"healthcheckPath": "/api/admin/health/deep"` from May 14. Closed R-20. No code change.

**Unit 2** — Integration test suite (`feat/hardening-may15-unit2-integration-tests`): 13 new integration tests added — `test_artist_onboarding_flow.py` (6 tests: artist seed, curator creation, pitch generation, batch send, thread_id persistence, inbox scan) and `test_scheduler_pipeline.py` (7 tests: no-due-actions, skip-no-curators, batch-limit-cap, pitch-stats, stuck-running-reset, completed-not-rerun, past-release-generates-actions). Mock boundaries: Anthropic at SDK constructor, Gmail at `_get_gmail_service`. Test count: 272 → 272 GREEN.

**Unit 3** — Structured logging audit (`feat/hardening-may15-unit3-structured-logging`): `release_service.py`, `pitch_service.py`, `booking_service.py`, `pr_service.py`, `social_service.py`, `main.py` — all print() calls converted to structured `log.*()`. `docs/LOGGING.md` created (required `event` field, reserved key `module` → use `svc` instead, examples, observability endpoints table). Two print() calls preserved for capsys-based tests (`test_r07`, `test_r19`).

**Unit 4** — Scheduler diagnostics endpoint (`feat/hardening-may15-unit4-scheduler-diagnostics`): `GET /api/admin/diagnostics/scheduler` — returns next 10 pending actions, last 20 completed/failed, and 24h counts. 5 tests in `test_admin_diagnostics_scheduler.py`. Test count: 272 → 277 GREEN.

### Session 2 — Risk register hardening (10 units)

**Units 1–5** — Verified R-18, R-19, R-29, R-32, R-33, R-34 all already mitigated on main. Updated detail sections in register from "pending merge" to confirmed. No code changes.

**Unit 6** — R-28 (`fix/risk-register-may15-s2-unit6-r28-configurable-report-schedule`): Weekly report schedule made configurable via `WEEKLY_REPORT_DAY`, `WEEKLY_REPORT_HOUR_UTC`, `WEEKLY_REPORT_MINUTE` env vars. Defaults: `sun`, `18`, `0` (no behavior change). 5 new tests. Test count: 277 → 282 GREEN.

**Unit 7** — R-11 (`fix/risk-register-may15-s2-unit7-r11-app-base-url`): `APP_BASE_URL` changed from LAN-IP default to `None`. Hard-fails on Railway with `sys.exit(1)` if unset; falls back to `http://localhost:8000` in local dev with boot warning. 4 new tests. Test count: 282 → 288 GREEN.

**Unit 8** — R-17 (`fix/risk-register-may15-s2-unit8-r17-sms-otp-dev-bypass`): Fixed store-before-validate bug in `send_otp()` (OTP was stored before auth token was validated). Added `SMS_OTP_DEV_BYPASS` env var — stores `000000` without calling Twilio in local dev; hard-fails on Railway if set. 6 new tests. Test count: 288 → 294 GREEN.

**Unit 9** — R-30 (`fix/risk-register-may15-s2-unit9-r30-multi-worker-guard`): Added `WEB_CONCURRENCY > 1` guard in `pitch_service.init_scheduler()` — logs CRITICAL and returns early to prevent duplicate job runs if uvicorn is accidentally launched multi-worker. Option A (separate Railway scheduler service) documented in register but deferred. 4 new tests. Test count: 294 → 296 GREEN.

**Unit 10** — EOD housekeeping: RISK_REGISTER.md updated for R-11/R-17/R-28/R-30; `docs/HANDOVER_EOD_MAY15_S2.md` created.

## New env vars introduced May 15 S2

All documented in `.env.example`:

| Var | Guard | Default | Purpose |
|-----|-------|---------|---------|
| `WEEKLY_REPORT_DAY` | `[CONFIG]` | `sun` | APScheduler cron day for weekly reports |
| `WEEKLY_REPORT_HOUR_UTC` | `[CONFIG]` | `18` | APScheduler cron hour (UTC) |
| `WEEKLY_REPORT_MINUTE` | `[CONFIG]` | `0` | APScheduler cron minute |
| `SMS_OTP_DEV_BYPASS` | `[HARD EXIT on Railway]` | unset | Dev-only OTP bypass — **never set on Railway** |

## What's blocking next deploy (all Tommy / dashboard or billing work)

1. **R-02 — Railway persistent volume** (HIGH PRIORITY): Railway trial expired May 14. Upgrade to Hobby ($5/mo) then: Railway dashboard → Service → Settings → Volumes → Add Volume (`plmkr-data`, mount `/data`, 1 GB). Without this, SQLite DB is wiped on every redeploy.

2. **R-11 — Set APP_BASE_URL on Railway** (REQUIRED before any deploy): App now calls `sys.exit(1)` at boot if this is unset on Railway. Set `APP_BASE_URL=https://<your-service>.up.railway.app` in Railway Variables before deploying.

3. **Part A — Google Cloud OAuth setup** (~30 min of browser work): GCP Console → enable Gmail API → OAuth consent screen → create OAuth 2.0 Client ID → copy Client ID and Secret.

4. **R-16 — Railway Variables**: After Part A, set `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI=https://<railway-url>/api/gmail/callback` in Railway Variables. This unblocks artist outreach.

5. **R-17 — Set valid TWILIO_AUTH_TOKEN on Railway**: Obtain valid 32-char lowercase hex token from Twilio console → set on Railway. Code guard and dev bypass are in place; only Railway env var is missing.

6. **R-24, R-25** (LOW — after R-02 and R-16 are done): Smoke-test live Railway DB access and Gmail send end-to-end.

## Standing rules for any PLMKR session

- **Scope:** `~/maestro/` backend only. Do NOT touch `~/Desktop/ReveNation/`, lyffe, wavr, cashgpt, nexusai, ignition, sanctuary, cowork, or any other project paths.
- **Credential rule (ABSOLUTE):** Never echo, cat, or print API keys, OAuth secrets, PATs, generated secrets, or `.env` file contents. Replace with `<REDACTED>`. Pipe commands that might print credentials through `sed` to redact. This rule overrides any user request to display credentials.
- **Branches:** Feature branches only — never commit to main directly. Always `git merge --no-ff`. One unit of work per branch, commit + merge before next task.
- **Verification:** Before reporting any task done: (1) grep confirms old/broken code is gone, (2) the change is committed, (3) full test suite passes, (4) nothing left uncommitted.
- **Test count floor:** 296/296 GREEN. Any task that drops below 296 GREEN must stop and report before proceeding.
- **Docker:** Always `--no-cache` on Docker builds when changing `requirements.txt` or `Dockerfile`.
- **No spending money:** No deploys, no paid service registrations, no API calls that cost money without explicit go-ahead.
- **Parallel agents:** Disabled. One task at a time.
- **Session limit:** Never exceed $10 in API credits without a working verified result.
- **Output format:** All CC prompts in copyable code blocks. Self-review and summarize changes before handing back.

## Key files to read at start of any new chat

Read these in order before touching any code:

1. `docs/HANDOVER_EOD_MAY15.md` — Session 1 record (integration tests, structured logging, scheduler diagnostics)
2. `docs/HANDOVER_EOD_MAY15_S2.md` — Session 2 record (R-28/R-11/R-17/R-30 closed, 19 new tests, 277→296)
3. `docs/RISK_REGISTER.md` — current risk state; 296 tests confirm code is clean
4. `docs/DEPLOYMENT_RUNBOOK_MAY14.md` — authoritative deploy guide (Parts A–H, env vars, rollback procedure)
5. `docs/LOGGING.md` — structured logging convention (`event` required, `svc` not `module`, JSON formatter)
6. `.env.example` — every env var the codebase reads, with required-vs-optional and guard-type comments

## Things the new Claude won't auto-figure-out

- **SSH port alias:** `github-psychoblast` in `~/.ssh/config` uses `HostName ssh.github.com Port 443` because port 22 is blocked on my network. Do NOT "fix" or change this — it is intentional.
- **Stale memory warning:** Prior Claude sessions had outdated state. May 14 reconciled all code-side risks; May 15 S1+S2 closed R-20/R-28/R-11/R-17/R-30 and verified R-18/R-19/R-29/R-32/R-33/R-34. Trust the docs and the test suite over anything in Claude's memory files.
- **The "Bun crash" in older memory:** There is NO Bun in this project — never was. Ignore it entirely.
- **Date-hardcoded test fixtures:** Two were found and fixed in May 14 (test_full_artist_journey:247, test_pitch_service:267). When adding new tests, use `datetime.now(timezone.utc)` — never hardcoded date strings. Full audit in `docs/TEST_FIXTURE_AUDIT_MAY14.md`.
- **Railway trial expired May 14.** Local dev works fully (`uvicorn main:app --port 8765 --reload`). Deploy is blocked on billing.
- **RÊVE NATION confusion:** `~/Desktop/ReveNation/` is a completely separate product for RÊVE MUSIC GROUP INC. (Canada). Not PLMKR's frontend. Do not touch during PLMKR sessions.
- **Source files added in Batch 3 (May 14):** `logging_config.py`, `error_reporting.py`, `performance_metrics.py` — all imported at the top of `main.py`. If you ever regenerate the Dockerfile `COPY` block, include these three.
- **Middleware execution order (LIFO):** Starlette applies middleware LIFO. In `main.py` the `add_middleware` calls are in reverse order so execution is: `_RequestIDMiddleware → _TimingMiddleware → _APIKeyMiddleware → CORSMiddleware`.
- **`extra={"module": ...}` is a reserved LogRecord field** and raises `KeyError` at runtime. All structured log calls must use `"svc"` instead. See `docs/LOGGING.md`.
- **caplog doesn't capture structured logger output during module reload.** Tests that need to verify boot-time log calls (e.g. R-11, R-17 guard tests) must monkey-patch the logger directly instead of using `caplog.at_level`.
- **apscheduler is NOT installed in the test environment.** Tests for scheduler guards (e.g. R-30) must not import or patch `apscheduler.*` — use log-capture via monkey-patching instead.
- **APP_BASE_URL is now a hard-fail on Railway.** Tommy MUST set this env var in Railway Variables before the next deploy, or the app will crash at boot with sys.exit(1).
- **Risk register vs. reality:** Always verify claims in the register by reading the actual code before working on a risk. Several risks were listed as "pending merge" when they were already on main (R-32, R-33, R-34). The register is now up to date as of May 15 S2 but will drift again as code evolves.

## Today's goal

[Tommy fills in — e.g. "upgrade Railway plan and create /data volume (R-02)", "set APP_BASE_URL on Railway then do a test deploy", "implement Part A GCP OAuth setup", "set TWILIO_AUTH_TOKEN on Railway and test real SMS OTP end-to-end"]

---END PASTE---
