# PLMKR — TODOS
Last updated: 2026-05-10 (May 10 session — Tier 1 risk mitigations complete)

---

## NEXT SESSION — TOP PRIORITY (do these before anything else)

1. **Merge 9 fix branches to main** — all Tier 1 mitigations from May 10 are on
   separate branches, none merged. See "RISK MITIGATIONS" section below. Suggested merge order:
   Dockerfile first (R-01), then service-code branches, then auth/CORS last.

2. **Railway redeploy + verify R-01 fix** — after merging fix/r01-dockerfile-service-files,
   trigger a Railway rebuild and `curl /api/admin/health/deep`. Must return service module
   status — not a 404 or "Application not found". This proves the dark-service issue is resolved.

3. **Set `APP_BASE_URL` on Railway** — currently defaults to `http://192.168.18.59:8765`
   (local dev IP, main.py:1826). Stripe success/cancel URLs and agent photo fallback
   URLs are broken in production until this is set to the Railway HTTPS URL.
   No code change needed — just set the env var and redeploy.

4. **Google Cloud OAuth setup (§3-A)** — create OAuth 2.0 Client ID on
   console.cloud.google.com, set `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`,
   `GMAIL_OAUTH_REDIRECT_URI` on Railway, redeploy.

5. **Replace 3–5 curator emails with real targets (§3-B)** — file: `data/curators_seed.json`.
   Do NOT do all 50 — fresh Gmail sender reputation risk.

6. **Verify Bug 1 on live Railway (§3-C)** — `GET /api/reports/weekly/{id}` must return
   `momentum_score`, `headline`, `highlights`. Migration auto-runs at boot (social_service.py:94).

7. **End-to-end Phase 1 Gmail test (§3-D)** — OAuth in browser → generate pitch →
   send to ONE real curator → confirm Sent folder → scan inbox → status = "replied".

---

## PHASE 0 — Foundation Fixes

| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.A | Voice ethnicity — all 16 agents match character | ✅ ON MAIN | `c7c1e2d` — 16 entries in _EL_VOICE_MAP, all unique |
| 0.B | Remove button language from skills + main.py | ✅ ON MAIN | `a8339e7` — grep zero hits confirmed May 8 |
| 0.C | Artist profile persistence — survive redeploy | ✅ ON MAIN | `dbe40e1` — Postgres or SQLite at /data/memory.db |
| 0.F | TTS audio cache persist on Railway volume | ✅ ON MAIN | `dd19298` — AUDIO_CACHE at /data/audio_cache |
| 0.F-2 | Static greeting always — remove has_history branch | ✅ ON MAIN | `6bc14b5` |
| 0.4 | Agent handoff — full context passed | ✅ ON MAIN | `37172f8` — profile + history + reason + actions |
| 0.1 | Voice mapping — fix in frontend CallScreen.js | 🔵 FRONTEND | Backend correct. Fix lives in ~/Desktop/[scrubbed]/ |
| 0.2 | Voice delay — verify /api/tts/synth wiring | 🔵 FRONTEND | Backend wired. Frontend verification pending |
| 0.3 | Audio stops on hangup — AbortController | 🔵 FRONTEND | Fix lives in ~/Desktop/[scrubbed]/ |
| 0.5 / 0.D | Twilio SMS OTP — real end-to-end test | 🔴 OPEN | Needs Tommy's physical device. Dev bypass active |
| 0.E | First call failure — audio/connect issue | 🔴 OPEN | Needs logcat from real device + reproduction steps |

### Phase 0 Backend: COMPLETE ✅
Frontend items (0.1/0.2/0.3) and device items (0.D/0.E) are separate concerns.
Backend sign-off was given May 8. Frontend/device session needed separately.

---

## PHASE 1 — Core Action Layer ✅ ON MAIN

All code committed and pushed. Railway auto-deploy should have picked up the code.
Gmail OAuth config is the remaining manual blocker (see §3-A + §3-D below).

| # | Task | Status | Commit | Notes |
|---|------|--------|--------|-------|
| 1.1 | Gmail OAuth routes + token storage | ✅ ON MAIN | `3452271` | GET /api/gmail/auth, /callback, /status |
| 1.2 | sendEmail() + token refresh | ✅ ON MAIN | `02e0026` | Auto-refresh on expiry, GmailNotConnected/GmailAuthExpired |
| 1.3 | Curator + Pitch + PitchInteraction DB + CRUD | ✅ ON MAIN | `02e0026` | SQLite tables + GET/POST/PATCH endpoints |
| 1.4 | 50 placeholder curators seed data | ✅ ON MAIN | `b46ff4c` | seed_curators.py + data/curators_seed.json |
| 1.5 | generatePitchEmail() — Claude Haiku | ✅ ON MAIN | `02e0026` | Marcus persona, JSON output, POST /api/pitches/generate |
| 1.6 | sendPitchEmails() batch orchestration | ✅ ON MAIN | `02e0026` | POST /api/pitches/batch |
| 1.7 | detectReplies() inbox poller | ✅ ON MAIN | `02e0026` | POST /api/inbox/scan |
| 1.8 | APScheduler polling — every 6h | ✅ ON MAIN | `02e0026` | Opt-in: SCHEDULER_ENABLED=true |
| 1.9 | Follow-up triggers day 1/3/5 | ✅ ON MAIN | `02e0026` | POST /api/pitches/followups/queue |
| test | Unit tests — 15 tests, mocked | ✅ ON MAIN | `02e0026` | tests/test_pitch_service.py |

### Phase 1 Remaining Manual Steps (Tommy)
1. ~~git push origin main~~ — done, code is on main ✅
2. Create Google Cloud OAuth credentials — **PENDING (§3-A)**
3. Set `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI` on Railway — **PENDING**
4. ~~Railway redeploy~~ — auto-deploys on push ✅
5. Run `POST /api/curators/seed` or `python3 seed_curators.py` on Railway shell — **PENDING**
6. Replace 3–5 placeholder emails — **PENDING (§3-B)**
7. Artist connects Gmail: `GET /api/gmail/auth?artist_id=ARTIST_ID` — **PENDING**
8. Test: `POST /api/pitches/batch` — **PENDING**
9. Set `SCHEDULER_ENABLED=true` when ready — **PENDING (§3-G)**

---

## PHASE 2 — PR & Booking Outreach Layer ✅ ON MAIN

All code committed and pushed. Unblocked once Gmail OAuth (Phase 1) is working.

| # | Task | Status | Commit | Notes |
|---|------|--------|--------|-------|
| 2.1 | PR contacts + outreach + interactions DB + CRUD | ✅ ON MAIN | `f1cefa6` | GET/POST/PATCH /api/pr-contacts, /api/pr-outreach |
| 2.2 | Booking contacts + inquiries + interactions DB + CRUD | ✅ ON MAIN | `f1cefa6` | GET/POST/PATCH /api/booking-contacts, /api/booking-inquiries |
| 2.3 | Seed data — 40 PR contacts + 30 booking contacts | ✅ ON MAIN | `f1cefa6` | seed_pr_contacts.py + seed_booking_contacts.py |
| 2.4 | Quinn (PR Manager) + Avery (Booking Agent) added | ✅ ON MAIN | `5fb05bc` | AGENTS list, greetings, AGENT ROSTER, skill files |
| 2.5 | generatePREmail() + generateBookingEmail() | ✅ ON MAIN | `f1cefa6` | Claude Haiku, JSON output |
| 2.6 | sendPREmails() + sendBookingEmails() batch | ✅ ON MAIN | `f1cefa6` | POST /api/pr-outreach/batch + /api/booking-inquiries/batch |
| 2.7 | detectPRReplies() + detectBookingReplies() + scan-all | ✅ ON MAIN | `f1cefa6` | POST /api/inbox/scan-all |
| 2.8 | PR follow-ups day 3+7 + booking follow-ups day 5+14 | ✅ ON MAIN | `f1cefa6` | POST /api/pr-outreach/followups/queue |
| 2.9 | Unit tests — 21 tests, mocked | ✅ ON MAIN | `f1cefa6` | test_pr_service.py + test_booking_service.py |

### Phase 2 Remaining Manual Steps (Tommy)
1. ~~git push origin main~~ — done ✅
2. ~~New DB tables~~ — auto-created at startup ✅
3. Seed PR contacts: `python3 seed_pr_contacts.py` (replace placeholder emails first) — **PENDING**
4. Seed booking contacts: `python3 seed_booking_contacts.py` (replace placeholder emails first) — **PENDING**
5. Test PR batch: `POST /api/pr-outreach/batch` — **PENDING** (needs Gmail OAuth first)
6. Test booking batch: `POST /api/booking-inquiries/batch` — **PENDING**
7. Test unified scan: `POST /api/inbox/scan-all?artist_id=ARTIST_ID` — **PENDING**

---

## PHASE 3 — Social Scheduling + Weekly Reports ✅ ON MAIN

All code committed and pushed. Buffer integration is MOCKED — posts are stored
in DB with `"mocked": True` and NOT published until Buffer OAuth is configured (§3-F).

| # | Task | Status | Commit | Notes |
|---|------|--------|--------|-------|
| 3.1 | SocialPost schema + CRUD endpoints | ✅ ON MAIN | `ac335fd` | GET/POST/PATCH/DELETE /api/social/posts/* |
| 3.2 | Buffer API integration | ✅ ON MAIN | `ac335fd` | OAuth stubs + _buffer_schedule_post() MOCKED — not live |
| 3.3 | Riley (Social Media Manager) agent + skill | ✅ ON MAIN | `fbf30d1` | AGENTS, greetings, roster, skill file |
| 3.4 | generateSocialPost() — Riley persona | ✅ ON MAIN | `ac335fd` | Claude Haiku, platform-specific limits |
| 3.5 | schedulePosts() batch orchestration | ✅ ON MAIN | `ac335fd` | POST /api/social/posts/batch |
| 3.6 | WeeklyReport schema + endpoints | ✅ ON MAIN | `ac335fd` | GET /api/reports/weekly, POST /api/reports/weekly/generate |
| 3.7 | generateWeeklyReport() — Claude Sonnet synthesis | ✅ ON MAIN | `ac335fd` | momentum_score 1-10, headline + insights + recommendations |
| 3.8 | Weekly report scheduler — Sundays 18:00 UTC | ✅ ON MAIN | `ac335fd` | Opt-in via SCHEDULER_ENABLED |
| 3.9 | Unit tests — 14 tests, 14/14 passing | ✅ ON MAIN | `50f0c0b` | test_social_service.py + test_reports.py |

### Phase 3 Remaining Manual Steps (Tommy)
1. ~~git push / redeploy / DB tables~~ — all done ✅
2. (Optional) Create Buffer app — **PENDING (§3-F, deferrable)**
3. Set `BUFFER_CLIENT_ID`, `BUFFER_CLIENT_SECRET`, `BUFFER_REDIRECT_URI` on Railway — **PENDING**
4. Test social post generation: `POST /api/social/posts/generate` — can test without Buffer ✅
5. Test weekly report: `POST /api/reports/weekly/generate?artist_id=ARTIST_ID` — can test without Buffer ✅

---

## PHASE 4 — Release Campaign Orchestration ✅ ON MAIN (May 9)

Shipped in the May 9 autonomous CC run. Merged to main via `fecbeec`.

| # | Task | Status | Commit | Notes |
|---|------|--------|--------|-------|
| 4.1 | release_service.py — Release schema + CRUD | ✅ ON MAIN | `dacadf5` | POST/GET/PATCH /api/releases |
| 4.2 | Campaign auto-scheduler — 8 action types across Phases 1–3 | ✅ ON MAIN | `dacadf5` | POST /api/releases/{id}/generate-campaign |
| 4.3 | execute-due — scan campaign_actions hourly | ✅ ON MAIN | `dacadf5` | POST /api/releases/{id}/campaign/execute-due |
| 4.4 | Sage agent (release-strategist) | ✅ ON MAIN | `dacadf5` | skills/maestro-release-strategist/SKILL.md |
| 4.5 | Admin stats + deep health endpoints | ✅ ON MAIN | `5419fe9` | GET /api/admin/stats, /api/admin/health/deep |
| 4.6 | Structured logging across outreach services | ✅ ON MAIN | `b16e251` | pitch/pr/booking services |
| 4.7 | Gmail 429 retry with exponential backoff | ✅ ON MAIN | `f4cbea9` | 1s/2s/4s, pitch_service.py |
| 4.8 | Idempotency keys on outreach sends | ✅ ON MAIN | `8ed0073` | pitches table unique constraint |
| 4.9 | 7 pre-existing test failures repaired | ✅ ON MAIN | `5f0b69e` | test_pitch_service.py |
| 4.10 | OpenAPI spec export (76 endpoints) | ✅ ON MAIN | `27a9374` | docs/openapi.json |
| 4.11 | Integration tests — release lifecycle | ✅ ON MAIN | `dacadf5` | tests/integration/test_release_lifecycle.py |
| Bug 1 | Persist momentum_score/headline/highlights | ✅ CODE FIXED — ⏳ RAILWAY UNVERIFIED | `7bab81e` | Migration auto-runs at boot (social_service.py:94). Verify: GET /api/reports/weekly/{id} must include all 3 fields. See §3-C. |

### Phase 4 Remaining Manual Steps
1. Set `SCHEDULER_ENABLED=true` to arm hourly execute-due — **PENDING (§3-G, last step)**

---

## RISK MITIGATIONS — May 10 (all pending merge to main)

10 units completed in session. 9 fix branches pushed to origin. **None merged yet.**

| Branch | Risk | What it fixes | Tests |
|--------|------|---------------|-------|
| `fix/r01-dockerfile-service-files` | R-01 | Dockerfile: add 6 service files + 3 seed scripts | — |
| `fix/b05-stripe-webhook-signature` | R-04 | Stripe webhook: enforce signature, env-gated dev bypass | 5 |
| `fix/c03-startup-running-reset` | R-07 | Reset stuck `running` campaign actions at startup | 1 |
| `fix/b01-anthropic-retry` | R-13 | Anthropic retry helper: 4 attempts, 1/2/4s backoff | 9 |
| `fix/b02-deterministic-idempotency` | R-08 | Idempotency keys: sha256(artist:contact:date) | 2 |
| `fix/b06-upload-size-limit` | R-14 | `/api/transcribe`: 25 MB cap + extension allowlist | 13 |
| `fix/b03-daily-send-quota` | R-09 | Per-artist 50/day send quota, SQLite-backed | 5 |
| `fix/r04-api-key-auth` | R-03 | X-API-Key middleware, dev-permissive if unset | 8 |
| `fix/b07-cors-lockdown` | R-15 | CORS: env-driven origin list, no wildcard | 8 |

Also: `docs/risk-register` (R-23 docs correction) and `docs/session-may10-final` (this file + session report).

New env vars introduced (set on Railway when ready to enforce):
- `PLMKR_API_KEY` — enable API key auth (unset = dev-permissive)
- `STRIPE_DEV_ALLOW_UNSIGNED` — set to `true` only in dev when no webhook secret
- `DAILY_PITCH_QUOTA` — per-artist daily send limit (default: 50)
- `MAX_UPLOAD_SIZE` — transcribe upload cap in bytes (default: 26214400 = 25 MB)
- `ALLOWED_ORIGINS` — comma-separated CORS origin list (default: Railway + Vercel + localhost)

---

## MANUAL CONFIG QUEUE — §3 (in execution order)

Nothing in this section requires new code. All are Railway/Google/Buffer dashboard tasks.

| Priority | Item | Status | Notes |
|----------|------|--------|-------|
| **1** | A. Google Cloud OAuth setup | 🔴 PENDING | ~30 min. console.cloud.google.com → create OAuth 2.0 Client ID (Web). Redirect URI: `https://maestro-backend-production-6d9c.up.railway.app/api/gmail/callback`. Set 3 Railway env vars + redeploy. |
| **2** | B. Replace 3–5 curator emails | 🔴 PENDING | File: `data/curators_seed.json`. 3–5 only first — sender rep risk. |
| **3** | C. Bug 1 Railway verification | 🔴 PENDING | `GET /api/reports/weekly/{id}` → confirm `momentum_score`, `headline`, `highlights` in response. |
| **4** | D. End-to-end Phase 1 Gmail test | 🔴 PENDING | Browser OAuth → generate → send to 1 curator → confirm Sent folder → scan inbox → status = "replied". |
| **5** | E. Phase 0 device items | 🔵 SEPARATE SESSION | Twilio OTP (0.D), logcat (0.E), CallScreen.js (0.1/0.2/0.3). Physical device + ~/Desktop/[scrubbed]/ required. |
| **6** | F. Buffer OAuth | 🟡 DEFERRABLE | buffer.com/developers/apps. Set `BUFFER_CLIENT_ID`, `BUFFER_CLIENT_SECRET`, `BUFFER_REDIRECT_URI`. Only needed when Phase 3 social scheduling goes live. |
| **7** | G. Enable scheduler | 🟡 LAST STEP | `SCHEDULER_ENABLED=true` on Railway. Arms: inbox poll 6h, weekly report Sundays 18:00 UTC, release execute-due hourly. Do after A–D verified. |

---

## CODE ISSUES SURFACED BY AUDIT (2026-05-10)

These were found during pre-flight read-only audit. No code changes made yet.
Review and decide disposition before next build session.

| # | Severity | File:line | Issue | Recommended action |
|---|----------|-----------|-------|--------------------|
| AU-1 | 🟡 MEDIUM | main.py:1826 | `APP_BASE_URL` defaults to `http://192.168.18.59:8765` (local dev IP). Stripe checkout success/cancel URLs and agent photo fallback URLs point there in production. | Set `APP_BASE_URL=https://maestro-backend-production-6d9c.up.railway.app` on Railway. No code change — env var only. |
| AU-2 | 🟡 MEDIUM | main.py:2114 | `GET /send-test-email` — unauthenticated endpoint, hardcoded recipient `yourpersonalemail@gmail.com`, uses legacy SMTP (`EMAIL_USER`/`EMAIL_PASS`). Dead dev scaffolding. | Delete the endpoint and the `EMAIL_USER`/`EMAIL_PASS` vars before production. |
| AU-3 | 🔵 INFO | social_service.py:930 | Weekly report scheduler hardcoded to UTC Sunday 18:00. No per-artist timezone support. | Note only. Acceptable for v1. |

Note: `ANTHROPIC_API_KEY` uses `os.environ[...]` (main.py:26) — hard crash at boot if absent.
This is correct behavior (intentional guard), not a bug. Just make sure it's always set on Railway.

---

## STANDING ITEMS

- [ ] Tommy to test 0.D (Twilio OTP) on real device
- [ ] Tommy to complete frontend 0.1/0.2/0.3 fixes in CallScreen.js (~/Desktop/[scrubbed]/)
- [ ] Decide: keep SQLite on /data volume or add Railway Postgres add-on (DATABASE_URL)
- [ ] Rotate any keys if exposed (check: ANTHROPIC, ELEVENLABS, TWILIO, STRIPE)
- [ ] Set `APP_BASE_URL` on Railway (AU-1 above — do before next Stripe test)
- [ ] Delete `/send-test-email` endpoint before production (AU-2 above)

---

## NOTES

- `ARTISTS_DIR` env var (main.py:33) is defined but unused — persistence uses SQLite/Postgres directly. Harmless. Remove in next cleanup pass.
- 43 total agents in AGENTS list; 16 have distinct EL voices in `_EL_VOICE_MAP`; rest use prefix fallback.
- `PLMKR_Master_PRD_v3.docx` in .gitignore (binary working doc, not versioned).
- Buffer `_buffer_schedule_post()` in social_service.py is a stub — `"mocked": True`. Posts are NOT published to Buffer until credentials are set and the stub is wired to the real API call.
- Tests: 78/78 passing on main as of May 9 merge (`fecbeec`). May 10 session added 51 more tests across 7 new/modified test files — all on fix branches, not yet merged.
