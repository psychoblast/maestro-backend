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

## Current state at end of May 14, 2026

- **main HEAD:** `5655991`
- **Tag:** `v0.1-eod-2026-05-14` → `5655991`
- **Test suite:** 259/259 GREEN (`python3 -m pytest -q` → 259 passed ~155s)
- **Risk register:** All 34 original code-side risks addressed. ~3 dashboard/env-var tasks remain for Tommy (not dev tasks).
- **Deploy status:** Local dev fully functional. Railway deploy BLOCKED — Railway trial expired May 14. Need $5/mo Hobby plan to create persistent volume (R-02).

## What was accomplished May 14 (four batches)

**Batch 1** — git author fix, `.env` mocks for build stage so env vars don't bleed into Docker build args, RISK_REGISTER fully reconciled against actual code (20 risks confirmed mitigated), R-20 deep-health readiness endpoint shipped (`/api/admin/health/deep`), full EOD handover doc created.

**Batch 2** — Fixed pre-existing `test_full_artist_journey:247` (hardcoded `2026-05-04` date broke after that date passed), R-19 Kokoro TTS startup warning (explicit boot message instead of silent failure), R-18 Whisper model prebaked in Dockerfile (eliminates 140 MB download on cold start), stale-docs cleanup (removed references to non-existent files), test hygiene audit (37 files, 225 tests — all green, no skip/xfail issues).

**Batch 3** — Structured logging foundation (`logging_config.py`: request-ID ContextVar, JSON/human formatter, ring buffer), admin diagnostics endpoint suite (`/api/admin/diagnostics`, `/api/admin/diagnostics/performance`, `/api/admin/diagnostics/anthropic-stats`, `/api/admin/diagnostics/gmail-stats`), Sentry-ready error hooks (`error_reporting.py`, no-op without DSN), request-timing middleware (`Server-Timing` header, slow-request WARNING, per-route p50/p95/p99), Anthropic + Gmail call observability (counters by model/artist, call-level logging — never logs prompt content), performance audit (N+1 inbox scan fixed in `pitch_service.py`, two deferred with PERF-MAY14 comments).

**Batch 4** — `docs/API_REFERENCE.md` generated from FastAPI routes (79 routes, 11 tag groups + coverage smoke test), `docs/LOCAL_DEVELOPMENT.md` (full local dev guide), `docs/DEPLOYMENT_RUNBOOK_MAY14.md` (authoritative deploy guide; `RUNBOOK_MANUAL_SESSION.md` banner'd HISTORICAL), test fixture audit (fixed naive datetime landmine in `test_pitch_service.py:267`), test runtime audit (module-scope fixture for `test_r12`, 155s suite documented as architecture-intrinsic).

## What's blocking next deploy (all Tommy / dashboard work)

1. **R-02 — Railway persistent volume** (HIGH PRIORITY): Railway trial expired May 14. Need to upgrade to Hobby ($5/mo) then: Railway dashboard → Service → Settings → Volumes → Add Volume (`plmkr-data`, mount `/data`, 1 GB). Without this, SQLite DB is wiped on every redeploy.

2. **R-20 follow-up** (can be done now in code): Edit `railway.json` line 8 — change `"healthcheckPath": "/health"` to `"healthcheckPath": "/api/admin/health/deep"` so Railway auto-restarts on DB failure. The deep endpoint is live and returns 503 when `db_connected=false`. This is a one-line code change, no Railway dashboard needed.

3. **Part A — Google Cloud OAuth setup** (~30 min of browser work): GCP Console → enable Gmail API → OAuth consent screen (App name: `PLMKR — Marquis Holdings LLC`, entity email: Tommy's call on which Gmail to use — recommendation: create a Marquis-aligned Gmail or use an existing one you control for the entity) → create OAuth 2.0 Client ID → copy Client ID and Secret.

4. **R-16 — Railway Variables**: After Part A, set `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI=https://<railway-url>/api/gmail/callback` in Railway Variables. This unblocks artist outreach.

5. **R-24, R-25** (LOW — after R-02 and R-16 are done): Smoke-test live Railway DB access and Gmail send end-to-end.

## Standing rules for any PLMKR session

- **Scope:** `~/maestro/` backend only. Do NOT touch `~/Desktop/ReveNation/`, lyffe, wavr, cashgpt, nexusai, ignition, sanctuary, cowork, or any other project paths.
- **Credential rule (ABSOLUTE):** Never echo, cat, or print API keys, OAuth secrets, PATs, generated secrets, or `.env` file contents. Replace with `<REDACTED>`. Pipe commands that might print credentials through `sed` to redact. This rule overrides any user request to display credentials.
- **Branches:** Feature branches only — never commit to main directly. Always `git merge --no-ff`. One unit of work per branch, commit + merge before next task.
- **Verification:** Before reporting any task done: (1) grep confirms old/broken code is gone, (2) the change is committed, (3) full test suite passes, (4) nothing left uncommitted.
- **Test count floor:** 259/259 GREEN. Any task that drops below 259 GREEN must stop and report before proceeding.
- **Docker:** Always `--no-cache` on Docker builds when changing `requirements.txt` or `Dockerfile`.
- **No spending money:** No deploys, no paid service registrations, no API calls that cost money without explicit go-ahead.
- **Parallel agents:** Disabled. One task at a time.
- **Session limit:** Never exceed $10 in API credits without a working verified result.
- **Output format:** All CC prompts in copyable code blocks. Self-review and summarize changes before handing back.

## Key files to read at start of any new chat

Read these in order before touching any code:

1. `docs/HANDOVER_EOD_MAY14.md` — full session record with all four batch sections, current risk state, Tommy's action items
2. `docs/DEPLOYMENT_RUNBOOK_MAY14.md` — authoritative deploy guide (Parts A–H, env vars, rollback procedure)
3. `docs/RISK_REGISTER.md` — current risk state; all original 34 risks accounted for
4. `docs/LOCAL_DEVELOPMENT.md` — local dev setup (prerequisites, venv, .env.local, pytest commands)
5. `docs/API_REFERENCE.md` — generated from FastAPI routes; 79 routes across 11 tag groups
6. `.env.example` — every env var the codebase reads, with required-vs-optional and guard-type comments

## Things the new Claude won't auto-figure-out

- **SSH port alias:** `github-psychoblast` in `~/.ssh/config` uses `HostName ssh.github.com Port 443` because port 22 is blocked on my network. Do NOT "fix" or change this — it is intentional.
- **Stale memory warning:** Prior Claude sessions had outdated state (Tier 2 tests unverified, Dockerfile broken, risk items marked as fixed when they weren't). May 14 reconciled all of it. Trust the docs over anything in Claude's memory files.
- **The "Bun crash" mentioned in older memory:** There is NO Bun in this project — never was. Whatever that referred to was a different project. Ignore it entirely.
- **Date-hardcoded test fixtures:** Two were found and fixed in May 14 sessions (test_full_artist_journey:247 and test_pitch_service:267). When adding new tests, use `datetime.now(timezone.utc).isoformat()` for "current time" fixtures, never hardcoded date strings. The full audit is in `docs/TEST_FIXTURE_AUDIT_MAY14.md`.
- **Railway trial expired May 14.** Local dev works fully (`uvicorn main:app --port 8765 --reload`). Deploy is blocked on billing. This is a business decision, not a code decision.
- **RÊVE NATION confusion:** The frontend at `~/Desktop/ReveNation/` is a completely separate product for RÊVE MUSIC GROUP INC. (Canada). It is not PLMKR's frontend. PLMKR is API-only for now. Do not touch that repo during PLMKR sessions.
- **New source files added in Batch 3:** `logging_config.py`, `error_reporting.py`, `performance_metrics.py` — all three are imported at the top of `main.py` before FastAPI app construction. If you ever regenerate the Dockerfile `COPY` block, include these three files.
- **Middleware execution order (LIFO):** Starlette applies middleware LIFO. In `main.py` the `add_middleware` calls are in reverse order so execution is: `_RequestIDMiddleware → _TimingMiddleware → _APIKeyMiddleware → CORSMiddleware`.

## Suggested first prompt for tomorrow's chat

```
Continuing PLMKR backend work. State at end of May 14, 2026:

- main HEAD: 5655991, tag v0.1-eod-2026-05-14
- Test suite: 259/259 GREEN
- Repo: ~/maestro/ (psychoblast/maestro-backend on GitHub)

Read these files first, in this order:
1. docs/HANDOVER_EOD_MAY14.md
2. docs/DEPLOYMENT_RUNBOOK_MAY14.md
3. docs/RISK_REGISTER.md

Today's goal: [Tommy fills in — e.g. "upgrade Railway plan and create the /data volume (R-02)" or "implement the railway.json healthcheckPath fix (R-20)" or "start Part A GCP OAuth setup walkthrough"]

Standing rules: PLMKR backend (~/maestro/) scope only. Credential rule enforced (no echoing keys). Feature branches, --no-ff merges, 259-test floor. Full rules in docs/HANDOVER_EOD_MAY14.md final section.
```

---END PASTE---
