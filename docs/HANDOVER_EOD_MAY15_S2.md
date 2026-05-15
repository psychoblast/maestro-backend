# PLMKR — EOD Handover May 15, 2026 — Session 2

**Session date:** 2026-05-15 (S2)
**Base tag:** `v0.1-eod-2026-05-15` (main `c45c16c`, 277 tests GREEN)
**End tag:** `v0.1-eod-2026-05-15-s2` (main after Unit 10 merge, 296 tests GREEN)
**Net new tests:** +19 (277 → 296)

---

## What Was Done Today (S2)

### Units 1–5 — Verification of R-18, R-19, R-29, R-32, R-33, R-34 ✅
**Branch:** `fix/risk-register-may15-s2-unit1to5-verify-r18-r19-r32-r33-r34` → merged `2698483`

All six risks were already mitigated on main from prior sessions. The RISK_REGISTER.md quick-reference table already showed them mitigated, but the R-32/R-33/R-34 detail sections still said "Mitigated — pending merge." Updated those detail sections to confirm the commits are on main and verified.

No code changes. Documentation-only.

**Test count:** 277/277 GREEN (unchanged)

---

### Unit 6 — R-28: Configurable weekly report schedule ✅
**Branch:** `fix/risk-register-may15-s2-unit6-r28-configurable-report-schedule` → merged `bc1bd41`
**Commit:** `43def81`

**Changes:**
- `social_service.py`: Added 3 module-level constants read from env vars at import time:
  ```python
  _WEEKLY_REPORT_DAY    = os.environ.get("WEEKLY_REPORT_DAY",      "sun").strip().lower()
  _WEEKLY_REPORT_HOUR   = int(os.environ.get("WEEKLY_REPORT_HOUR_UTC", "18"))
  _WEEKLY_REPORT_MINUTE = int(os.environ.get("WEEKLY_REPORT_MINUTE",   "0"))
  ```
  `init_report_scheduler()` passes these to `add_job`. Defaults preserve existing v1 behavior (Sunday 18:00 UTC).
- `.env.example`: Added `WEEKLY_REPORT_DAY`, `WEEKLY_REPORT_HOUR_UTC`, `WEEKLY_REPORT_MINUTE` under `[CONFIG]`.
- `tests/test_r28_configurable_report_schedule.py`: **New** — 5 tests covering default schedule, custom day/hour/minute, missing env vars, and log event.

**Test count after:** 282/282 GREEN

---

### Unit 7 — R-11: APP_BASE_URL hard-fail on Railway ✅
**Branch:** `fix/risk-register-may15-s2-unit7-r11-app-base-url` → merged `18a6a12`
**Commit:** `5cdcd0d`

**Changes:**
- `main.py`: Changed `APP_BASE_URL` default from LAN IP to `None`. Added guard:
  - If `APP_BASE_URL is None` and `_on_railway` → `sys.exit(1)` with a clear fatal message (mirrors `STRIPE_DEV_ALLOW_UNSIGNED` pattern).
  - If `APP_BASE_URL is None` in local dev → falls back to `http://localhost:8000` with structured `boot_warning` log.
- `tests/test_r11_app_base_url.py`: **New** — 4 tests (Railway sys.exit, localhost fallback, explicit URL accepted, Railway with URL accepted).
- `tests/test_b05_stripe_dev_flag_prod_guard.py`: Added `APP_BASE_URL=https://test.railway.app` to `_load_app()` helper to prevent R-11 guard from interfering with Stripe guard tests.
- `.env.example`: Updated `APP_BASE_URL` guard comment to `[HARD EXIT on Railway]`.

**Test count after:** 288/288 GREEN

---

### Unit 8 — R-17: SMS_OTP_DEV_BYPASS guard + store-before-validate fix ✅
**Branch:** `fix/risk-register-may15-s2-unit8-r17-sms-otp-dev-bypass` → merged `9f3d79a`
**Commit:** `a3d0d11`

**Changes:**
- `main.py`:
  - **Store-before-validate bug fixed:** Auth token validation now runs BEFORE OTP is stored in `_otp_store`. Malformed token returns 503 without creating a store entry.
  - **`SMS_OTP_DEV_BYPASS` guard added** (after Stripe guard, same pattern): If `SMS_OTP_DEV_BYPASS=true` and `_on_railway` → `sys.exit(1)` at boot. In local dev → structured `boot_warning` log.
  - **Dev bypass path in `send_otp()`:** When `SMS_OTP_DEV_BYPASS=true`, stores code `000000` without calling Twilio; returns `{"status": "ok"}`.
- `tests/test_r17_sms_otp_dev_bypass.py`: **New** — 6 tests:
  - Malformed token → 503
  - OTP not stored on bad token (validates store-before-validate fix)
  - Railway + bypass → sys.exit(1)
  - Local dev + bypass → 200 with status ok
  - verify-otp accepts 000000 after bypass send
  - No bypass + no Twilio → 503
- `.env.example`: Added `SMS_OTP_DEV_BYPASS` under Twilio section as `[HARD EXIT on Railway]`; updated `TWILIO_AUTH_TOKEN` comment to note format validation.

**Test count after:** 294/294 GREEN

---

### Unit 9 — R-30: Multi-worker scheduler guard ✅
**Branch:** `fix/risk-register-may15-s2-unit9-r30-multi-worker-guard` → merged `d603d12`
**Commit:** `4607eb4`

**Changes:**
- `pitch_service.py`: Added WEB_CONCURRENCY guard in `init_scheduler()` after the `SCHEDULER_ENABLED` check:
  ```python
  web_concurrency = int(os.environ.get("WEB_CONCURRENCY", "1") or "1")
  if web_concurrency > 1:
      log.critical("scheduler_disabled", extra={
          "event":       "scheduler_disabled",
          "reason":      "WEB_CONCURRENCY > 1 — scheduler skipped to prevent duplicate job runs",
          "concurrency": web_concurrency,
      })
      return
  ```
  Option A (separate Railway scheduler service) documented in RISK_REGISTER.md but out of scope for v1.
- `tests/test_r30_multi_worker_guard.py`: **New** — 4 tests using `log.critical` monkey-patching (avoids apscheduler import):
  - `WEB_CONCURRENCY=2` → CRITICAL logged, `_scheduler` stays None
  - `WEB_CONCURRENCY=1` → guard does not fire
  - `WEB_CONCURRENCY` unset → guard does not fire
  - `SCHEDULER_ENABLED=false` → guard never reached

**Test count after:** 296/296 GREEN

---

### Unit 10 — EOD handover (this file) ✅
**Branch:** `fix/risk-register-may15-s2-unit10-eod-handover`

**Changes:**
- `docs/RISK_REGISTER.md`:
  - Header updated (Last updated, Sources)
  - Quick-reference table: R-11, R-17, R-28 → Mitigated; R-30 → Partially mitigated
  - Detail sections: R-11, R-17, R-28 updated with "✅ MITIGATED" and commit hashes; R-30 header updated with "⚠️ PARTIALLY MITIGATED"
- `docs/HANDOVER_EOD_MAY15_S2.md`: This file.

---

## Current Test Floor

| Suite | Count | Status |
|-------|-------|--------|
| All tests (`python3 -m pytest tests/`) | **296** | ✅ GREEN |
| Integration tests (`tests/integration/`) | 13 | ✅ GREEN |
| Unit tests | 283 | ✅ GREEN |

---

## New Env Vars Introduced This Session

| Var | Guard | Default | Purpose |
|-----|-------|---------|---------|
| `WEEKLY_REPORT_DAY` | `[CONFIG]` | `sun` | APScheduler cron day for weekly reports |
| `WEEKLY_REPORT_HOUR_UTC` | `[CONFIG]` | `18` | APScheduler cron hour (UTC) for weekly reports |
| `WEEKLY_REPORT_MINUTE` | `[CONFIG]` | `0` | APScheduler cron minute for weekly reports |
| `SMS_OTP_DEV_BYPASS` | `[HARD EXIT on Railway]` | unset | Dev-only OTP bypass; hard-fails on Railway |

All four documented in `.env.example`.

---

## Git State

```
main HEAD: <tag v0.1-eod-2026-05-15-s2 pending>
Branch: fix/risk-register-may15-s2-unit10-eod-handover (pre-merge)
Uncommitted changes: none (after unit10 commit)
Unpushed commits: S2 Units 6–10 (10 commits + 5 merge commits since v0.1-eod-2026-05-15)
```

**Do NOT push to origin without Tommy's explicit instruction.** Tommy will run:
```
git push origin main
git push origin v0.1-eod-2026-05-15-s2
```

---

## Open Risks (Tommy actions required)

| ID | Risk | Action |
|----|------|--------|
| R-02 | `/data` ephemeral — Railway volume not confirmed | Create Railway persistent volume in dashboard; verify `railway.toml` mounts at `/data` |
| R-11 | `APP_BASE_URL` not set on Railway | Set `APP_BASE_URL=https://<your-service>.up.railway.app` in Railway Variables — **app will crash on deploy without this** |
| R-16 | Gmail OAuth not configured | Set `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI` on Railway |
| R-17 | Valid Twilio token not yet set | Set valid `TWILIO_AUTH_TOKEN` (32 lowercase hex chars) from Twilio console on Railway |
| R-24 | Bug 1 fix unverified on live Railway DB | Check live Railway DB |
| R-25 | Campaign execute-due not smoke-tested vs live Gmail | Test with live Gmail account after OAuth configured |

---

## Risks Now Fully Code-Mitigated (Tommy no longer needs to act for code correctness)

| ID | Old Status | New Status | What changed |
|----|-----------|-----------|--------------|
| R-28 | Accepted | ✅ Mitigated | Schedule configurable via env vars; defaults unchanged |
| R-11 | Open | ✅ Mitigated | Code hard-fails on Railway if unset; Tommy still must SET the var |
| R-17 | Open | ✅ Mitigated | Store-before-validate fixed; bypass guard added; Tommy still must SET valid token |
| R-30 | Accepted | ⚠️ Partially mitigated | Option B guard in `init_scheduler()`; Option A out of scope for v1 |

---

## What's Next

The risk register now has only 6 open/Tommy-action items remaining (all requiring Railway dashboard or live-service actions, not code changes). The test floor is at 296 GREEN.

Recommended next session priorities:

1. **Gmail OAuth flow** (R-16) — `GET /api/gmail/auth` already returns 503 when credentials unset; Tommy needs to configure GCP OAuth and set env vars. After that, the pitch/PR/booking pipeline can be smoke-tested end-to-end.
2. **Set `APP_BASE_URL` on Railway** (R-11) — Required before any Stripe checkout testing. App will crash on deploy without it.
3. **Rotate Twilio auth token** (R-17) — Set valid 32-hex-char token on Railway; test send-otp with a real phone.
4. **Confirm Railway persistent volume** (R-02) — Dashboard check; no code change needed.

---

## Key Files Added / Changed This Session

| File | Change |
|------|--------|
| `social_service.py` | `_WEEKLY_REPORT_DAY/HOUR/MINUTE` env-var constants; `init_report_scheduler()` uses them |
| `main.py` | `APP_BASE_URL` hard-fail guard (R-11); `SMS_OTP_DEV_BYPASS` guard + send_otp store-before-validate fix (R-17) |
| `pitch_service.py` | `WEB_CONCURRENCY > 1` guard in `init_scheduler()` (R-30) |
| `.env.example` | New vars documented: `WEEKLY_REPORT_*`, `SMS_OTP_DEV_BYPASS`; updated comments for `APP_BASE_URL`, `TWILIO_AUTH_TOKEN` |
| `tests/test_r28_configurable_report_schedule.py` | **New** — 5 tests |
| `tests/test_r11_app_base_url.py` | **New** — 4 tests |
| `tests/test_b05_stripe_dev_flag_prod_guard.py` | Added `APP_BASE_URL` to `_load_app()` helper |
| `tests/test_r17_sms_otp_dev_bypass.py` | **New** — 6 tests |
| `tests/test_r30_multi_worker_guard.py` | **New** — 4 tests |
| `docs/RISK_REGISTER.md` | R-11/R-17/R-28/R-30 updated (quick-reference + detail sections + header) |
| `docs/HANDOVER_EOD_MAY15_S2.md` | **This file** |
