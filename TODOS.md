# PLMKR — TODOS
Last updated: 2026-05-08 (autonomous session)

---

## PHASE 0 — Foundation Fixes

| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.A | Voice ethnicity — all 16 agents match character | ✅ COMMITTED | `c7c1e2d` — 16 entries in _EL_VOICE_MAP, all unique |
| 0.B | Remove button language from skills + main.py | ✅ COMMITTED | `a8339e7` — grep zero hits confirmed May 8 |
| 0.C | Artist profile persistence — survive redeploy | ✅ COMMITTED | `dbe40e1` — Postgres or SQLite at /data/memory.db |
| 0.F | TTS audio cache persist on Railway volume | ✅ COMMITTED | `dd19298` — AUDIO_CACHE at /data/audio_cache |
| 0.F-2 | Static greeting always — remove has_history branch | ✅ COMMITTED | `6bc14b5` |
| 0.4 | Agent handoff — full context passed | ✅ COMMITTED | `37172f8` — profile + history + reason + actions |
| 0.1 | Voice mapping — fix in frontend CallScreen.js | 🔵 FRONTEND | Backend correct. Frontend fix pending Tommy |
| 0.2 | Voice delay — verify /api/tts/synth wiring | 🔵 FRONTEND | Backend wired. Frontend verification pending |
| 0.3 | Audio stops on hangup — AbortController | 🔵 FRONTEND | Frontend fix pending Tommy |
| 0.5 / 0.D | Twilio SMS OTP — real end-to-end test | 🔴 OPEN | Needs Tommy's physical device. Dev bypass still active |
| 0.E | First call failure — audio/connect issue | 🔴 OPEN | Needs logcat from Tommy's device + reproduction steps |

### Phase 0 Readiness for Phase 1
- Backend Phase 0 items: ALL COMMITTED ✅
- Remaining blockers are frontend (Tommy's device + CallScreen.js) or require Tommy
- Tommy sign-off needed before Phase 1 begins (per CLAUDE.md protocol)

---

## PHASE 1 — Core Action Layer (IMPLEMENTED LOCALLY — needs Tommy deploy)

All units in `pitch_service.py`. Router wired into `main.py`. See `SESSION_NOTES_MAY8.md` for deploy checklist.

| # | Task | Status | Commit | Notes |
|---|------|--------|--------|-------|
| 1.1 | Gmail OAuth routes + token storage | ✅ LOCAL | `3452271` | GET /api/gmail/auth, /callback, /status |
| 1.2 | sendEmail() + token refresh | ✅ LOCAL | `02e0026` | Auto-refresh on expiry, GmailNotConnected/GmailAuthExpired errors |
| 1.3 | Curator + Pitch + PitchInteraction DB + CRUD | ✅ LOCAL | `02e0026` | SQLite tables + GET/POST/PATCH endpoints |
| 1.4 | 50 placeholder curators seed data | ✅ LOCAL | `b46ff4c` | seed_curators.py + data/curators_seed.json |
| 1.5 | generatePitchEmail() — Claude Haiku | ✅ LOCAL | `02e0026` | Marcus persona, JSON output, POST /api/pitches/generate |
| 1.6 | sendPitchEmails() batch orchestration | ✅ LOCAL | `02e0026` | POST /api/pitches/batch — generate + save + send |
| 1.7 | detectReplies() inbox poller | ✅ LOCAL | `02e0026` | POST /api/inbox/scan — thread match + Claude classify |
| 1.8 | APScheduler polling — every 6h | ✅ LOCAL | `02e0026` | Opt-in: SCHEDULER_ENABLED=true |
| 1.9 | Follow-up triggers day 1/3/5 | ✅ LOCAL | `02e0026` | POST /api/pitches/followups/queue, tier-based thresholds |
| test | Unit tests (15 tests, all mocked) | ✅ LOCAL | `02e0026` | tests/test_pitch_service.py, no real creds needed |

### Phase 1 Deploy Checklist (Tommy does this)
1. `git push origin main` — push 6 local commits
2. Create Google Cloud OAuth credentials (see .env.example)
3. Set GMAIL_OAUTH_CLIENT_ID, GMAIL_OAUTH_CLIENT_SECRET, GMAIL_OAUTH_REDIRECT_URI on Railway
4. Railway redeploy (auto-deploys on push if GitHub connected)
5. Run `python3 seed_curators.py` on Railway shell OR hit POST /api/curators/seed
6. Replace all placeholder@example.com emails in curators table with real curator emails
7. Artist connects Gmail: GET /api/gmail/auth?artist_id=ARTIST_ID
8. Test pitch: POST /api/pitches/batch
9. Set SCHEDULER_ENABLED=true when ready for automatic inbox polling

---

## PHASE 2 — PR & Booking Outreach Layer (IMPLEMENTED LOCALLY — needs Tommy deploy)

All units split between `pr_service.py` and `booking_service.py`. Routers wired into `main.py`.

| # | Task | Status | Commit | Notes |
|---|------|--------|--------|-------|
| 2.1 | PR contacts + outreach + interactions DB + CRUD | ✅ LOCAL | `f1cefa6` | GET/POST/PATCH /api/pr-contacts, /api/pr-outreach |
| 2.2 | Booking contacts + inquiries + interactions DB + CRUD | ✅ LOCAL | `f1cefa6` | GET/POST/PATCH /api/booking-contacts, /api/booking-inquiries |
| 2.3 | Seed data — 40 PR contacts + 30 booking contacts | ✅ LOCAL | `f1cefa6` | seed_pr_contacts.py + seed_booking_contacts.py |
| 2.4 | Quinn (PR Manager) + Avery (Booking Agent) added | ✅ LOCAL | `5fb05bc` | AGENTS list, greetings, AGENT ROSTER, skill files |
| 2.5 | generatePREmail() Quinn persona + generateBookingEmail() Avery persona | ✅ LOCAL | `f1cefa6` | Claude Haiku, JSON output |
| 2.6 | sendPREmails() + sendBookingEmails() batch orchestration | ✅ LOCAL | `f1cefa6` | POST /api/pr-outreach/batch + /api/booking-inquiries/batch |
| 2.7 | detectPRReplies() + detectBookingReplies() + unified scan-all | ✅ LOCAL | `f1cefa6` | POST /api/pr-outreach/scan + /api/booking-inquiries/scan + /api/inbox/scan-all |
| 2.8 | PR follow-ups day 3+7 + booking follow-ups day 5+14 | ✅ LOCAL | `f1cefa6` | POST /api/pr-outreach/followups/queue + /api/booking-inquiries/followups/queue |
| 2.9 | Unit tests — 21 tests, all mocked | ✅ LOCAL | `f1cefa6` | tests/test_pr_service.py + tests/test_booking_service.py, 21/21 passing |

### Phase 2 Deploy Checklist (Tommy does this)
1. `git push origin main` — push local commits (f1cefa6, 5fb05bc) to origin
2. Railway auto-deploys on push
3. New DB tables created automatically at startup
4. `python3 seed_pr_contacts.py` — seed 40 PR contacts (replace placeholder emails first)
5. `python3 seed_booking_contacts.py` — seed 30 booking contacts (replace placeholder emails first)
6. Artist connects Gmail (if not already): GET /api/gmail/auth?artist_id=ARTIST_ID
7. Test PR batch: POST /api/pr-outreach/batch
8. Test booking batch: POST /api/booking-inquiries/batch
9. Test unified scan: POST /api/inbox/scan-all?artist_id=ARTIST_ID

---

## STANDING ITEMS

- [ ] Tommy to test 0.D (Twilio OTP) on real device
- [ ] Tommy to review frontend 0.1/0.2/0.3 fixes in CallScreen.js
- [ ] Tommy to sign off Phase 0 complete before Phase 1 begins
- [ ] Decide whether to set DATABASE_URL (Railway Postgres add-on) or keep SQLite on volume
- [ ] Rotate any keys if exposed (check: ANTHROPIC, ELEVENLABS, TWILIO, STRIPE)

---

## NOTES

- `ARTISTS_DIR` env var (line 33 main.py) is defined but unused — persistence now uses SQLite/Postgres directly. Harmless, but can be removed.
- 42 total agents in AGENTS list (added Quinn + Avery); 16 have distinct EL voices in _EL_VOICE_MAP; rest use prefix fallback.
- `PLMKR_Master_PRD_v3.docx` added to .gitignore (binary working doc, not versioned).
