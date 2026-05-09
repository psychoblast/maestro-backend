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

## PHASE 1 — Core Action Layer (NOT STARTED)

See `PHASE1_PLAN.md` for full implementation outline.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Gmail OAuth — routes + token storage | ⬜ PLANNED | See PHASE1_PLAN.md |
| 1.2 | Gmail token refresh logic | ⬜ PLANNED | |
| 1.3 | sendEmail() core function | ⬜ PLANNED | |
| 1.4 | Curator data model + SQLite table | ⬜ PLANNED | |
| 1.5 | Curator seed data (initial list) | ⬜ PLANNED | |
| 1.6 | Inbox parsing — read/categorize emails | ⬜ PLANNED | |
| 1.7 | Marcus pitching agent — function calling | ⬜ PLANNED | |
| 1.8 | Press database | ⬜ PLANNED | |
| 1.9 | Venue database | ⬜ PLANNED | |

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
- 40 total agents in AGENTS list; 16 have distinct EL voices in _EL_VOICE_MAP; rest use prefix fallback.
- `PLMKR_Master_PRD_v3.docx` added to .gitignore (binary working doc, not versioned).
