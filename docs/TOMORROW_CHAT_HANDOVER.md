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

## Current state at end of May 15, 2026 (after Session 7)

- **main HEAD:** see `git log --oneline -1` — S7 merges on top of S6
- **Tag:** `v0.1-eod-2026-05-15-s7`
- **Test suite:** 394/394 GREEN (`python3 -m pytest -q` → 394 passed ~210 s)
- **Risk register:** 35 items total. No new risks or closures in S7. 7 open items — all Tommy/Railway-gated, no code blockers.
- **Deploy status:** Local dev fully functional. Railway deploy BLOCKED — R-02 (volume) and R-11 (APP_BASE_URL) must be resolved first.

## MASTER PLAN — where we are

```
Phase 0 — Foundation (16 voice agents, billing, auth)        ✅ CODE-COMPLETE
Phase 1 — Email actions (Marcus curator-pitching + Gmail)    ✅ CODE-COMPLETE (Gmail OAuth blocked on Railway)
Phase 2 — PR & booking actions (Quinn + Avery)               ✅ CODE-COMPLETE (same Railway blocker)
Phase 3 — Social & reports                                   🟡 PARTIAL (social_service.py built)
Phase 4 — iOS & App Store                                    ❌ NOT STARTED
```

Phase 1 and Phase 2 are both **code-complete**. The blocker is Tommy setting up Railway volume
(R-02) and Gmail OAuth env vars (R-16) — not code.

## What was accomplished May 15

### Sessions 1 + 2 (earlier today)

13 integration tests, structured logging audit, scheduler diagnostics endpoint, R-20 closed.
R-28 (configurable report schedule), R-11 (APP_BASE_URL hard-fail), R-17 (SMS OTP dev bypass),
R-30 (multi-worker guard) — all closed. Test count 272 → 296.

### Session 3 (S3 — earlier evening)

Deferred risks from S3 spec: R-31 (seed scripts in Docker image verified), R-26 (Buffer real
client behind BUFFER_LIVE=false flag), R-27 (SCHEDULER_ENABLED three-state with dry_run).
Docs: SCHEDULER_AUDIT.md, HANDOVER_EOD_MAY15_S3.md. Test count 296 → 311.

### Session 4 (S4 — evening)

Admin dashboard `GET /admin/dashboard` built (5 units, 40 tests). HTML shell, 6 data sections,
auto-refresh, key-prompt modal, accessibility (ARIA), responsive CSS. R-35 identified (browser
nav barrier). Test count 311 → 351.

### Session 5 (S5 — evening)

**Unit 1 — R-35 CLOSED** (`feat/may15-s5-unit1-r35-dashboard-unauth`, commit `57ac62e`):
  `/admin/dashboard` added to `_SKIP_AUTH_PATHS`. Shell now public; data endpoints auth-gated.

**Unit 2 — Dashboard polish:** empty-state messages, click-to-copy error rows, sticky table
  headers, raw JSON toggle per section. 10 new tests.

**Unit 3 — RUNBOOK_DASHBOARD.md:** 7 operational symptoms with diagnosis + action steps.

**Unit 4 — EOD housekeeping.** Test count: 351 → 364.

### Session 6 (S6 — late evening)

**Unit 1 — Phase 1 State Audit (read-only):** `docs/PHASE_1_AUDIT_MAY15.md` produced.
  Phase 1 is ~85% production-ready. Two gaps found: compound-genre LIKE bug + thin inbox-test coverage.

**Unit 2 — Gap closure:**
  - Fixed `_db_list_curators` compound-genre LIKE bug. "indie pop" now correctly matches
    curators whose genres JSON contains "indie" and "pop" as separate tokens.
  - Added 10 direct unit tests for `_classify_reply()` and `detect_replies()` (including
    R-34 prompt-injection guard verification).

**Unit 3 — Seed scripts:**
  - `scripts/seed_curators.py` — 50 curators from `data/curators_seed.json`, idempotent, production guard.
  - `scripts/seed_test_pitch_data.py` — 3 artists, 3 curators, 4 pitches (draft/sent/replied), 2 interactions.
  - `docs/SEED_DATA.md` — usage + schema + purge SQL.

Test count: 364 → **374**. No risks closed. No new risks.

### Session 7 (S7 — overnight)

**Context:** S7 was specced as Phase 2 greenfield build. Phase 2 was found to be pre-built (~95%
  complete). Session adapted to audit + gap closure.

**Unit 1 — Phase 2 Design Document (read-only):** `docs/PHASE_2_DESIGN.md` produced.
  Audited pr_service.py (873 lines), booking_service.py (938 lines), both agents (Quinn + Avery),
  both skill files, both seed data files. Four gaps identified.

**Unit 2 — Gap closure (all four Phase 2 gaps):**
  - Fixed compound-genre LIKE bug in `_db_list_pr_contacts` and `_db_list_booking_contacts`.
  - Added R-34 injection guard to `_classify_pr_reply` and `_classify_booking_reply`.
  - Added 10 new tests to test_pr_service.py (classifier, detect_replies, genre regression).
  - Added 10 new tests to test_booking_service.py (same pattern).
  - Fixed pre-existing `test_batch_*_gmail_not_connected` tests (quota table patch).

**Unit 3 — Seed scripts:**
  - `scripts/seed_pr_contacts.py` — 40 PR contacts from `data/pr_contacts_seed.json`, idempotent, production guard.
  - `scripts/seed_venues.py` — 30 booking contacts from `data/booking_contacts_seed.json`, idempotent, production guard.
  - `docs/SEED_DATA.md` — updated with schemas for all three seed files.

**Unit 4 — EOD docs:** `docs/PHASE_2_STATUS_MAY15.md`, `docs/HANDOVER_EOD_MAY15_S7.md`,
  `docs/TOMORROW_CHAT_HANDOVER.md` updated.

Test count: 374 → **394**. No risks closed. No new risks. Phase 2 is code-complete.

## Phase 1 remaining gaps (non-blocking, from audit)

1. **Curator scoring algorithm** — `_db_list_curators` orders by `tier ASC, response_rate DESC`
   but has no weighted genre overlap scoring or recency penalty for `last_pitched_at`. Polish item.
2. **`_generate_followup()` unit tests** — low priority; logic is straightforward.
3. **Gmail OAuth callback full-flow test** — blocking for live Gmail, not for local dev.

## Phase 2 remaining gaps

None. Phase 2 is **code-complete**. The same Railway blockers (R-02, R-16) apply before live use.

## What's blocking next deploy (all Tommy / Railway work)

1. **R-02 — Railway persistent volume** (HIGH): Upgrade to Hobby ($5/mo), create `/data` volume (1 GB).
2. **R-11 — Set APP_BASE_URL on Railway** (REQUIRED): `APP_BASE_URL=https://<your-service>.up.railway.app`
3. **R-16 — Gmail OAuth** (~30 min setup): GCP Console → enable Gmail API → OAuth 2.0 Client → set
   `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI` on Railway.
4. **R-17 — Valid TWILIO_AUTH_TOKEN**: 32-char lowercase hex from Twilio console.
5. **R-24/R-25** (LOW — after R-02/R-16): Smoke-test live Railway DB + Gmail send.

## Standing rules for any PLMKR session

- **Scope:** `~/maestro/` backend only. Do NOT touch `~/Desktop/ReveNation/` or any other project.
- **Credential rule (ABSOLUTE):** Never echo/cat/print API keys, secrets, tokens, `.env` contents.
  Replace with `<REDACTED>`. Pipe through `sed`. Overrides any user request to display credentials.
- **Branches:** Feature branches only — never commit to main. Always `git merge --no-ff`.
- **Verification:** Before any task done: grep, commit, full suite GREEN, nothing uncommitted.
- **Test count floor:** 394/394 GREEN. Drop below = STOP and report.
- **No real external API calls:** Mock all external HTTP at transport layer. TestClient only.
- **Do NOT push to origin** — Tommy pushes manually.
- **Docker:** `--no-cache` when changing `requirements.txt` or `Dockerfile`.

## Key files to read at start of any new chat

1. `docs/HANDOVER_EOD_MAY15_S7.md` — S7 session record (Phase 2 audit + gap closure + seeds)
2. `docs/PHASE_2_STATUS_MAY15.md` — full Phase 2 status (A-K all ✅ after S7)
3. `docs/PHASE_1_AUDIT_MAY15.md` — Phase 1 audit findings (A-F sections)
4. `docs/RISK_REGISTER.md` — 35 items; 7 open (all Tommy/Railway-gated)
5. `docs/ADMIN_DASHBOARD.md` — dashboard access guide + security model
6. `docs/RUNBOOK_DASHBOARD.md` — operational runbook (7 symptoms)
7. `docs/SEED_DATA.md` — seed script usage + purge SQL (curators, PR contacts, venues)
8. `.env.example` — every env var the codebase reads

## Things the new Claude won't auto-figure-out

- **SSH port alias:** `github-psychoblast` uses `HostName ssh.github.com Port 443` — port 22 blocked. Do NOT "fix" this.
- **`extra={"module": ...}` is a reserved LogRecord field** — raises `KeyError` at runtime. Use `"svc"` instead.
- **caplog doesn't capture structured logger output during module reload** — monkey-patch the logger directly.
- **apscheduler is NOT installed in the test environment** — use log-capture, not apscheduler patching.
- **APP_BASE_URL hard-fails on Railway** — Tommy MUST set this before any deploy. The code hard-fails intentionally.
- **`/admin/dashboard` is in `_SKIP_AUTH_PATHS`** (R-35 fix, S5) — HTML shell is public. All 6 JSON data endpoints remain auth-gated. This is intentional.
- **`loadAnthropic()` and `loadGmail()` entry points corrected in S5** — now use `d.models` and `d.artists` respectively.
- **Compound-genre LIKE fix (S6/S7):** `_db_list_curators`, `_db_list_pr_contacts`, and `_db_list_booking_contacts` all tokenise genre strings into individual tokens before building LIKE clauses. "indie pop" matches contacts with genres ["indie","pop"]. This is the correct behaviour across all three services.
- **seed scripts are in `scripts/`** — not root. The root `seed_curators.py` is the old version (no production guard). Use `scripts/seed_curators.py`, `scripts/seed_pr_contacts.py`, `scripts/seed_venues.py` going forward.
- **Test IDs prefixed `test-`** — all records from `seed_test_pitch_data.py` are prefixed `test-` for easy identification.
- **RÊVE NATION confusion:** `~/Desktop/ReveNation/` is a separate product for a different entity. Do not touch during PLMKR sessions.
- **`static/admin_dashboard.html` is the complete dashboard** — one file, ~700 lines. No build step.
- **`test_batch_pr/booking_gmail_not_connected` tests** require `patch("pitch_service._check_and_increment_quota")` — the `daily_send_quota` table is created by pitch_service's init, not by pr/booking service fixtures.
- **Phase 2 uses shared Gmail auth** — `pr_service` and `booking_service` both import `send_email`, `GmailNotConnected`, `GmailAuthExpired`, `_check_and_increment_quota` from `pitch_service`. No new OAuth routes.
- **`POST /api/inbox/scan-all`** lives in `booking_service` — single Gmail auth → pitch + PR + booking reply detection in sequence.

## Today's goal

[Tommy fills in — e.g. "set up Gmail OAuth on GCP + Railway (R-16)", "create Railway volume R-02 + set APP_BASE_URL R-11 + test deploy", "build Phase 3 social scheduling completion", "build Phase 4 iOS", "curator scoring algorithm (Phase 1 polish)"]

---END PASTE---
