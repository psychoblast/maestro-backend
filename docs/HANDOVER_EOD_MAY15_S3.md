# PLMKR — EOD Handover: May 15, 2026 — Session 3 (Evening)

**Session tag:** `v0.1-eod-2026-05-15-s3`  
**Base commit at session start:** `2e59156` (main, `v0.1-eod-2026-05-15-s2`)  
**Test floor at session start:** 296/296 GREEN  
**Test floor at session end:** 311/311 GREEN (+15 new tests)

---

## What Was Done

### Unit 1 — R-31: Seed scripts in Docker image (MITIGATED)

**Branch:** `feat/deferred-risks-may15-s3-unit1-r31-seed-scripts`  
**Commits:** `4e6e4ac` → merged `ee79d94`

- Confirmed `seed_curators.py`, `seed_pr_contacts.py`, `seed_booking_contacts.py` already present in `Dockerfile:22-24` COPY block
- Added `Makefile` with `build-test` and `verify-seeds-in-image` targets
- Verified all three seeds land at `/app/` in Docker image via `make verify-seeds-in-image IMAGE=plmkr-seed-check`
- Added `docs/DEPLOYMENT_RUNBOOK_MAY14.md` **Part I: Running DB Seeds Against Railway** — documents API-endpoint-first path and Railway shell alternative
- Fixed `RISK_REGISTER.md` quick-reference: R-31 `Open` → `Mitigated`

### Unit 2 — R-27: Scheduler audit (AUDIT COMPLETE)

**Branch:** `feat/deferred-risks-may15-s3-unit2-r27-scheduler-audit`  
**Commits:** `2a3b47d` → merged `1e1b305`

- Static code audit of all three scheduler jobs — no scheduler started, all findings from source reading
- `docs/SCHEDULER_AUDIT.md` produced with full callgraphs, side effects, risk levels:
  - `inbox_poll`: interval 6h, **MEDIUM** (Gmail reads + Anthropic + SQLite, no emails sent)
  - `weekly_reports`: cron Sun 18:00 UTC, **MEDIUM** (Anthropic + SQLite, no emails)
  - `campaign_executor`: interval 1h, **HIGH** (real emails via Gmail + Anthropic)
- **STOP-SHIP jobs: 0** → Unit 3 cleared
- Flip-the-switch checklist (Phase 1 verify → Phase 2 dry_run → Phase 3 true) included in doc

### Unit 3 — R-27: Scheduler three-state flag (PARTIALLY MITIGATED)

**Branch:** `feat/deferred-risks-may15-s3-unit3-r27-scheduler-enable`  
**Commits:** `96a54c4` → merged `bfeb15f`

**New `SCHEDULER_ENABLED` states:**

| Value | Behavior |
|-------|----------|
| unset / false | Scheduler does not start (existing safe default) |
| `dry_run` | Scheduler starts; jobs log `would_have_fired`, no emails / API calls |
| `true` | Fully live; sends real emails via Gmail |

**Files changed:**
- `pitch_service.py`: `_SCHEDULER_DRY_RUN` flag; `_poll_all` extracted from closure to module level with dry_run guard; `init_scheduler()` starts in both true and dry_run modes
- `social_service.py`: `_SCHEDULER_DRY_RUN` flag; `_generate_all_weekly_reports()` dry_run guard
- `release_service.py`: `_SCHEDULER_DRY_RUN` flag; `execute_all_due_campaign_actions()` dry_run guard
- `main.py`: `_SCHEDULER_ENABLED_FLAG` includes `dry_run` for campaign_executor registration
- `.env.example`: three-state documented with ramp guidance
- `tests/test_r27_scheduler_dry_run.py`: 6 tests (unset/dry_run/live paths) — all GREEN

### Unit 4 — R-26: Buffer real HTTP client (PARTIALLY MITIGATED)

**Branch:** `feat/deferred-risks-may15-s3-unit4-r26-buffer-integration`  
**Commits:** `762830b` → merged `e00339c`

**New routing in `_buffer_schedule_post()`:**

| Condition | Behavior |
|-----------|----------|
| `BUFFER_LIVE=false` (default) or `BUFFER_API_KEY` unset | Mock response (safe) |
| `SCHEDULER_ENABLED=dry_run` | Log `would_have_posted`, return mock |
| `BUFFER_LIVE=true` + `BUFFER_API_KEY` set | Real `_buffer_post_real()` call |

**`_buffer_post_real()` features:**
- `async with httpx.AsyncClient(timeout=httpx.Timeout(10.0))` — async, non-blocking
- 429 rate-limit retry: 2 retries, exponential backoff (2s → 4s)
- Non-200 error logged and raised
- Malformed JSON response logged and raised
- Structured logging on every path

**Files changed:**
- `social_service.py`: `import asyncio` + `import httpx` at top; `_BUFFER_API_KEY`/`_BUFFER_LIVE` flags; `_buffer_post_real()` added; `_buffer_schedule_post()` rewritten
- `.env.example`: `BUFFER_LIVE` and `BUFFER_API_KEY` documented with ramp guidance
- `tests/test_r26_buffer_live_client.py`: 9 tests covering all routing branches — all GREEN

---

## What Was Verified

| Check | Result |
|-------|--------|
| 311/311 tests GREEN | ✅ |
| R-31 Docker seed scripts at `/app/` | ✅ `make verify-seeds-in-image IMAGE=plmkr-seed-check` |
| R-27 dry_run: no real API calls | ✅ 6 tests assert mocked clients not called |
| R-26 BUFFER_LIVE=false: no HTTP | ✅ 9 tests assert httpx not called when flag off |
| No real Gmail/Anthropic/Buffer calls this session | ✅ All HTTP mocked at transport layer |
| Commits on feature branches, merged --no-ff to main | ✅ |

---

## What Is Still Open

### Tommy must do to enable scheduler (R-27):

1. Confirm Railway persistent volume is attached (`/data` mount) — R-02
2. Set `GMAIL_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI` on Railway — R-16
3. Authorize Gmail for at least one test artist
4. Review curator/PR/booking seed data for real email addresses
5. Set `SCHEDULER_ENABLED=dry_run` on Railway — observe 24h, confirm `would_have_fired` in logs
6. Set `SCHEDULER_ENABLED=true` + `SCHEDULER_BATCH_LIMIT=1` — observe first tick
7. Full checklist in `docs/SCHEDULER_AUDIT.md` → "Flip-the-Switch Checklist"

### Tommy must do to enable Buffer live (R-26):

1. Complete Buffer OAuth flow for at least one artist (`GET /api/buffer/auth?artist_id=<id>`)
2. Set `BUFFER_LIVE=true` + `BUFFER_API_KEY=<access-token>` on Railway
3. Test with one artist, one post before wider rollout

### Still open infrastructure risks (not addressed this session):

- **R-02**: Railway persistent volume — Tommy must confirm in Railway dashboard
- **R-16**: Gmail OAuth — Tommy must set env vars and authorize at least one artist
- **R-24**: Bug 1 live Railway DB check (requires live access)
- **R-25**: Campaign execute-due smoke test against live Gmail (requires live access)

---

## Next Session Priorities

1. **R-02**: Confirm Railway volume attached — without this, DB wipes on every redeploy
2. **R-16**: Configure Gmail OAuth on Railway — without this, all outreach and scheduler are inert
3. Enable `SCHEDULER_ENABLED=dry_run` on Railway — first live observation of scheduler behavior
4. Any new feature work the user identifies

---

## Session Metrics

| Metric | Value |
|--------|-------|
| Tests at start | 296/296 |
| Tests at end | 311/311 |
| New tests added | 15 (6 R-27 + 9 R-26) |
| Risks addressed | R-31 ✅, R-27 ⚠️, R-26 ⚠️ |
| Branches created | 4 feature branches + Unit 5 |
| Commits to main | 8 (4 feature + 4 merges) |
| Real API calls | 0 (all mocked) |
