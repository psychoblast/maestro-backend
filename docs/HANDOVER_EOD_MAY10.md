# PLMKR Handover — End of Day May 10, 2026

## Session ID

- Date: 2026-05-10 (Sunday)
- Main commit at session end: `a525f8a`
- Tag: `v0.1-eod-2026-05-10`
- Backup: `~/maestro-backup-2026-05-10.tar.gz` (714 MB flat-file, excludes `.git`)

---

## What Got Done Today

The session opened expecting a manual Railway configuration walkthrough (Parts A–H of the runbook). An upfront audit instead revealed that the backend was in a deeper broken state than thought — the Dockerfile was missing every Phase 1–4 service file, meaning Railway would boot a shell with no actual application logic. That finding triggered a full risk-mitigation sprint. Five tiers of fixes were shipped across the day, each on its own feature branch with red-green test verification: Tier 1 fixed the hard blockers (Dockerfile, auth, Stripe, CORS, upload limits, graceful degradation); Tier 2 addressed scheduler and idempotency risks; Tier 3 added loud failure modes for migrations, Postgres failover, error envelopes, crash-state recovery, and prompt injection hardening; Tier 4 produced the Railway deploy runbook (Parts A–H) and a Tier 4 risk audit that surfaced three new findings; Tier 5 fixed those findings (list-join prompt injection, async event-loop blocking, and reply-classifier injection). The session ended with all branches merged to main, 217/218 tests green, a tagged snapshot, and a runbook ready to execute.

### Tier-by-Tier Table

| Tier | What It Covered | Key Branches | Tests Added |
|------|-----------------|--------------|-------------|
| 1 | Dockerfile (R-01), API key auth (R-03/R-04), CORS lockdown (R-15), upload limits (R-14), graceful degradation (R-05), send-test-email removal (R-12), Anthropic retry (R-13), scheduler backfill (R-10), daily send quota (B-03), deterministic idempotency (B-02), Stripe dev guard (B-05), CORS test (B-07) | `fix/r01`, `fix/r03`, `fix/r04`, `fix/r05`, `fix/r10`, `fix/r12`, `fix/r13`, `fix/r14`, `fix/r15`, `fix/b01`–`b07` | +66 |
| 2 | Per-artist timezone (F-01), per-artist volume staging (R-02 railway.toml), persistent-volume path audit | `fix/f01-per-artist-timezone`, `fix/r02-persistent-volume-staging` | +11 |
| 3 | Loud migration failures (R-21), Postgres failover (R-06), 422/HTTPException passthrough (R-22), crash-state recovery (R-07), prompt injection v1 (R-23) | `fix/r21`, `fix/r06`, `fix/r22`, `fix/r07`, `fix/r23` | +38 |
| 4 | Runbook (Parts A–H), quick reference card, Tier 4 risk audit (R-32/R-33/R-34 identified) | `docs/runbook-manual-session` | 0 (docs only) |
| 5 | List-join prompt injection (R-32), async event-loop blocking (R-33), reply-classifier injection (R-34) | `fix/r32`, `fix/r33`, `fix/r34` | +30 |
| Docs | Risk register, session reports, verification reports, TODOS reconciliation | `docs/risk-register`, `docs/session-may10-*`, `docs/verification-may10`, `docs/r31-cleanup` | 0 (docs only) |

**Total:** 32 branches merged to main today. Tests: baseline 132 → final 217 (1 pre-existing integration-test failure unrelated to today's work — `test_full_artist_journey` in `tests/integration/`).

---

## Current State of Main

- **Commit:** `a525f8a` — `[merge] docs/session-may10-tier5`
- **Tag:** `v0.1-eod-2026-05-10`
- **Tests:** 217 passing / 1 pre-existing failure (`tests/integration/test_full_artist_journey` — asserts on DB state that requires a real outreach cycle; pre-dates today's work)
- **Python compile:** all `.py` files compile clean

### What Is Working (Code-Complete)

- FastAPI on Railway — auto-deploys from main on GitHub push
- All Phase 1–4 service files present in Dockerfile: `pitch_service.py`, `pr_service.py`, `booking_service.py`, `social_service.py`, `release_service.py`, `admin_service.py`, `prompt_safety.py`
- `PLMKR_API_KEY` auth middleware in place (R-03/R-04 mitigated)
- Stripe webhook signature verification required by default (B-05 mitigated)
- CORS lockdown — only `ALLOWED_ORIGIN` env var passes (R-15 mitigated)
- Upload size limit + extension allowlist on `/api/transcribe` (R-14 mitigated)
- Anthropic retry with async exponential backoff — `_anthropic_call_with_retry()` in `anthropic_utils.py` (R-13, R-33 mitigated)
- Prompt injection sanitization on all user-controlled prompt fields (R-23, R-32, R-34 mitigated)
- Crash-state recovery: `campaign_actions` rows reset `running→pending` at startup (R-07 mitigated)
- Loud migration and Postgres-failover errors (R-21, R-06 mitigated)
- Per-artist timezone for weekly reports (F-01 mitigated)
- Scheduler backfill coalescing + per-tick batch limit (R-10 mitigated)
- `railway.toml` with `[volumes]` stanza for `/data` — staging config is committed

### What Is Mocked / Not Yet Wired

- **Gmail OAuth:** Not configured on Railway — all pitch/PR/booking outreach is blocked until Part F of the runbook is completed per artist
- **Twilio:** Auth token in Railway env is invalid format; SMS OTP dev bypass is active
- **Buffer integration:** Social posts generated but not published (accepted risk R-26)
- **Scheduler:** Disabled — no timed jobs active until Part H of runbook (R-27 accepted)
- **Kokoro TTS:** Model files not on Railway (R-19)
- **Whisper model:** Re-downloads ~140 MB on cold start (R-18)

### What Still Requires a Manual Railway Action

- **Persistent volume mount:** `railway.toml` has the stanza; Railway dashboard "Add Volume" must be clicked before first deploy (R-02)
- **`APP_BASE_URL` env var:** Must be set to the Railway-assigned URL (R-11)
- **Gmail OAuth per artist:** Follow Part F of runbook for each artist account (R-16)
- **Twilio auth token:** Rotate to a valid 32-char hex token (R-17)

---

## Tomorrow's First Move

Open `docs/RUNBOOK_MANUAL_SESSION.md` and follow **Parts A through H** in order. Phase 1 goes live after Parts A–F are complete. The quick reference card is at `docs/MANUAL_SESSION_QUICK_REF.md` — print it or keep it open in a second window. The runbook is the canonical instruction set; this handover is context only.

```
cat docs/MANUAL_SESSION_QUICK_REF.md
```

---

## Risk Register State

**Total items:** 34 | **Mitigated today:** 19 | **Open dev backlog:** 9 | **Open manual/operator items:** 6 | **Accepted:** 4 | **Docs-only / N/A:** 2

Full register: `docs/RISK_REGISTER.md`

### 6 Manual Items Blocking Phase 1 Live

These require Tommy action during the manual Railway session — no code change can fix them:

| ID | Blocker |
|----|---------|
| R-02 | Add persistent volume in Railway dashboard (`/data` mount) before first deploy |
| R-11 | Set `APP_BASE_URL` env var to Railway-assigned URL (currently defaults to local LAN IP) |
| R-16 | Complete Gmail OAuth per artist (Part F of runbook) — all outreach blocked until done |
| R-17 | Rotate Twilio auth token to valid 32-char hex; remove SMS dev bypass |
| R-24 | Verify Bug 1 fix on live Railway DB (not just local) |
| R-25 | Smoke-test campaign `execute-due` against live Gmail account after R-16 complete |

### 3 Dev Backlog Items Worth Knowing (Not Phase 1 Blockers)

| ID | Risk |
|----|------|
| R-08 | Idempotency keys do not prevent duplicate sends if the same action fires twice in rapid succession |
| R-09 | No rate limiting on batch send — a large batch can exhaust Anthropic quota in one tick |
| R-29 | APScheduler interval jobs have no `misfire_grace_time` — a slow tick silently drops the next fire |

---

## Files a New Claude Chat Should Read First

In priority order:

1. `docs/HANDOVER_EOD_MAY10.md` — this file
2. `docs/RUNBOOK_MANUAL_SESSION.md` — master deploy runbook (Parts A–H)
3. `docs/MANUAL_SESSION_QUICK_REF.md` — one-page print card
4. `docs/RISK_REGISTER.md` — all 34 risks with current status
5. `docs/RUNBOOK_RAILWAY_VOLUME.md` — volume setup sub-runbook (called from Part A)
6. `docs/SESSION_REPORT_MAY10.md` — historical detail (optional)
7. `CLAUDE.md` — build protocol (mandatory before touching code)

---

## Standing Rules That Survived Today

- **Never commit to main from CC sessions** — always create a feature branch, verify, then merge explicitly
- **Sanitize anything that could print credentials** before running (env vars, API keys, tokens)
- **Run `python3 -m py_compile` after every merge conflict resolution** — catches indentation and keyword bugs in seconds, before they reach Railway
- **All CC prompts that include shell commands must be copyable code blocks** — no narrative-only instructions
- **One unit at a time; verify before moving on** — never batch fixes into a single commit
- **Frontend at `~/Desktop/ReveNation/` is a separate session and a separate concern** — never touch from a `~/maestro/` session

---

## What Was Painful and Worth Not Repeating

- **Merge conflict + silent indent corruption:** During early conflict resolutions a `sed`/manual edit cycle corrupted indentation in `main.py`, which only surfaced at Railway boot (not local pytest). Fix: `python3 -m py_compile` after every conflict resolution catches this in seconds locally.
- **CC pushed to main once under autonomous mode:** Despite the standing rule to never push to main, an autonomous-mode prompt that didn't explicitly name the target branch resulted in a direct push. Fix: prompts must explicitly name the target branch in each unit's instructions, not rely on a standing rule the model may not surface in context.
- **Bun runtime crash mid-cumulative test:** A Bun process crash wiped the in-progress cumulative branch state. Fix: durable state on GitHub branches recovered cleanly — the lesson is to push branches before running long cumulative tests, not to rely on local state surviving.

---

## Project-Level Position (Situational Awareness for New Chat)

- **Repo:** `maestro-backend` — owned by `psychoblast` on GitHub, deployed to Railway
- **Frontend:** `~/Desktop/ReveNation/` — `psychoblast/plmkr-frontend` on GitHub. **Never touch from a `~/maestro/` session.**
- **Phase 0** (foundation): ~70% done. Frontend voice/audio items still open.
- **Phase 1** (curator pitching): code-complete on main, deploy-blocked on the 6 manual items above.
- **Phases 2/3/4** (PR outreach, booking, social): code-complete, all blocked downstream of Phase 1 going live.
- **Backend overall:** closest it has ever been to production-ready. The manual Railway session tomorrow is the gate between "code-complete" and "live."

---

## End of Handover
