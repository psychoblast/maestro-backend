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

## Current state at end of May 15, 2026 (after Session 5)

- **main HEAD:** see `git log --oneline -1` — multiple S5 merges on top of S4
- **Tag:** `v0.1-eod-2026-05-15-s5`
- **Test suite:** 364/364 GREEN (`python3 -m pytest -q` → 364 passed ~340 s)
- **Risk register:** 35 items total. R-35 newly mitigated (S5). 6 open items — all Tommy/Railway-gated, no code blockers.
- **Deploy status:** Local dev fully functional. Railway deploy BLOCKED — R-02 (volume) and R-11 (APP_BASE_URL) must be resolved first. All code is ready to deploy.

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

### Session 5 (S5 — current session)

**Unit 1 — R-35 CLOSED** (`feat/may15-s5-unit1-r35-dashboard-unauth`, commit `57ac62e`):
  `/admin/dashboard` added to `_SKIP_AUTH_PATHS`. Shell now public; data endpoints auth-gated.
  No browser extension needed. 3 new auth tests.

**Unit 2 — Dashboard polish** (`feat/may15-s5-unit2-dashboard-polish`):
  4 of 6 items: empty-state messages (.empty-state class), click-to-copy error rows
  (navigator.clipboard + #copy-toast), sticky table headers (.table-wrap), raw JSON toggle
  per section (_rawStore + .json-toggle-btn). 10 new tests.

**Unit 3 — RUNBOOK_DASHBOARD.md** (`feat/may15-s5-unit3-runbook-dashboard`):
  7 operational symptoms with diagnosis + action steps. First-time setup section.

**Unit 4 — EOD housekeeping** (current):
  R-35 closed in risk register, HANDOVER_EOD_MAY15_S5.md created, TOMORROW_CHAT_HANDOVER.md
  updated, tag v0.1-eod-2026-05-15-s5.

Test count: 351 → **364**. Delta S5: +13.

## New env vars introduced (none in S5)

No new env vars in S5. All env vars still documented in `.env.example`.

## What's blocking next deploy (all Tommy / Railway work)

1. **R-02 — Railway persistent volume** (HIGH PRIORITY): Upgrade to Hobby ($5/mo) then:
   Railway → Service → Settings → Volumes → Add Volume (`plmkr-data`, mount `/data`, 1 GB).
   Without this, SQLite DB is wiped on every redeploy.

2. **R-11 — Set APP_BASE_URL on Railway** (REQUIRED before any deploy): App calls `sys.exit(1)`
   at boot if unset. Set `APP_BASE_URL=https://<your-service>.up.railway.app` in Railway Variables.

3. **Part A — Google Cloud OAuth setup** (~30 min): GCP Console → enable Gmail API → OAuth
   consent screen → create OAuth 2.0 Client ID → copy Client ID + Secret. (R-16)

4. **R-16 — Railway Variables**: After Part A: set `GMAIL_OAUTH_CLIENT_ID`,
   `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI` in Railway Variables.

5. **R-17 — Valid TWILIO_AUTH_TOKEN**: Obtain 32-char lowercase hex token from Twilio console.

6. **R-24/R-25** (LOW — after R-02/R-16): Smoke-test live Railway DB + Gmail send.

## Standing rules for any PLMKR session

- **Scope:** `~/maestro/` backend only. Do NOT touch `~/Desktop/ReveNation/` or any other project.
- **Credential rule (ABSOLUTE):** Never echo/cat/print API keys, secrets, tokens, `.env` contents.
  Replace with `<REDACTED>`. Pipe through `sed`. Overrides any user request to display credentials.
- **Branches:** Feature branches only — never commit to main. Always `git merge --no-ff`.
- **Verification:** Before any task done: grep, commit, full suite GREEN, nothing uncommitted.
- **Test count floor:** 364/364 GREEN. Drop below = STOP and report.
- **No real external API calls:** Mock all external HTTP at transport layer. TestClient only.
- **Do NOT push to origin** — Tommy pushes manually.
- **Docker:** `--no-cache` when changing `requirements.txt` or `Dockerfile`.

## Key files to read at start of any new chat

1. `docs/HANDOVER_EOD_MAY15_S5.md` — S5 session record (R-35 closed, 4 polish items, runbook)
2. `docs/RISK_REGISTER.md` — 35 items; 6 open (all Tommy/Railway-gated)
3. `docs/ADMIN_DASHBOARD.md` — dashboard access guide + security model
4. `docs/RUNBOOK_DASHBOARD.md` — operational runbook (7 symptoms)
5. `docs/LOGGING.md` — structured logging convention
6. `.env.example` — every env var the codebase reads

## Things the new Claude won't auto-figure-out

- **SSH port alias:** `github-psychoblast` uses `HostName ssh.github.com Port 443` — port 22 blocked. Do NOT "fix" this.
- **`extra={"module": ...}` is a reserved LogRecord field** — raises `KeyError` at runtime. Use `"svc"` instead.
- **caplog doesn't capture structured logger output during module reload** — monkey-patch the logger directly.
- **apscheduler is NOT installed in the test environment** — use log-capture, not apscheduler patching.
- **APP_BASE_URL hard-fails on Railway** — Tommy MUST set this before any deploy.
- **`/admin/dashboard` is now in `_SKIP_AUTH_PATHS`** (R-35 fix, S5) — HTML shell is public. All 6 JSON data endpoints remain auth-gated. This is intentional.
- **`loadAnthropic()` and `loadGmail()` entry points corrected in S5** — now use `d.models` and `d.artists` respectively instead of `Object.entries(d)` on the whole response.
- **RÊVE NATION confusion:** `~/Desktop/ReveNation/` is a separate product for a different entity. Do not touch during PLMKR sessions.
- **`static/admin_dashboard.html` is the complete dashboard** — one file, ~700 lines. No build step.

## Today's goal

[Tommy fills in — e.g. "upgrade Railway plan and create /data volume (R-02)", "set APP_BASE_URL on Railway then do a test deploy", "implement GCP OAuth setup for Gmail (R-16)", "browser-test the dashboard on Railway"]

---END PASTE---
