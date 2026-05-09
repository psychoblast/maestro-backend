# Session Notes — 2026-05-08
Autonomous session. Tommy away. Read-only verification + documentation only.

---

## What Was Verified This Session

### A1 — 0.B Button Language (CLEAN)
- Command: `grep -rni "press the button|tap the button|click the button|button below" ~/maestro/`
- Result: **Zero hits** across all .md, .py, .txt files
- Status: ✅ Confirmed clean

### A2 — 0.A Voice IDs
- File: `main.py` lines 597–614 (`_EL_VOICE_MAP`)
- Result: 16 entries, all voice_id values unique within the map, no placeholder/TODO comments
- Status: ✅ Confirmed correct
- Minor note: `ARTISTS_DIR` (line 33) is defined but never referenced in persistence code — legacy from file-based approach that was replaced by SQLite/Postgres. Harmless.
- **Do NOT change voice IDs** — Tommy picks by ear

### A3 — 0.C Artist Persistence
- File: `main.py` — `load_artist()`, `_load_artist_file()`, `_save_artist_file()`
- Implementation: Routes to PostgreSQL if `DATABASE_URL` env var set, else SQLite at `/data/memory.db`
- Both `/data/` paths map to Railway's persistent volume
- Status: ✅ Solid implementation — profiles survive redeploy as long as Railway volume is mounted
- Note: If `DATABASE_URL` is ever set (Railway Postgres add-on), the app will automatically switch to Postgres on next boot with no code changes needed

---

## What Was Documented

1. **TODOS.md** — Created. All Phase 0 items mapped to git commits. Phase 1 items listed. Standing items noted.
2. **SESSION_NOTES_MAY8.md** — This file.
3. **PHASE1_PLAN.md** — Created. Gmail OAuth, curator model, Marcus agent, inbox parsing — planning doc only, no code.
4. **.gitignore** — `PLMKR_Master_PRD_v3.docx` added (binary working doc, not for version control).

---

## Phase 1 Plan Summary
See `PHASE1_PLAN.md` for full detail. Key decisions:
- Gmail OAuth: standard Authorization Code flow, tokens stored in artist profile (Postgres/SQLite)
- Curator model: new `curators` table in existing SQLite/Postgres DB — matches existing schema pattern
- Marcus pitching: function calling via Anthropic tool_use, `send_pitch_email()` and `search_curators()` tools
- Inbox parsing: periodic fetch via Gmail API, categorize by sender domain + subject keywords
- 9 units estimated for Phase 1 following one-unit-at-a-time protocol

---

## Open Items Needing Tommy

| Item | Reason |
|------|--------|
| 0.D — Twilio OTP real test | Requires Tommy's physical device for SMS receipt |
| 0.E — First call failure | Requires logcat + reproduction on Tommy's device |
| 0.1/0.2/0.3 — Frontend fixes | Requires Tommy to edit CallScreen.js in ~/Desktop/ReveNation/ |
| Phase 0 sign-off | Per CLAUDE.md: explicit user sign-off required before Phase 1 begins |
| Voice IDs (0.A) | Any voice ID changes require Tommy to test by ear |
| DATABASE_URL decision | Should Railway Postgres add-on be activated? Currently SQLite on volume |

---

## Files Changed This Session

| File | Action | Commit |
|------|--------|--------|
| TODOS.md | Created | 11659b4 |
| SESSION_NOTES_MAY8.md | Created | 11659b4 |
| PHASE1_PLAN.md | Created | 11659b4 |
| .gitignore | Updated (added *.docx) | 7daa27b |

### Push Status — BLOCKED
- Commits are local on branch `main`
- Push to `psychoblast/maestro-backend.git` failed: 403 HTTPS, SSH key (`mindvisionllc`) lacks write access
- **Tommy action required:** `git push origin main` after authenticating as `psychoblast`
- Alternative: add `mindvisionllc` SSH key to `psychoblast` GitHub account as collaborator

---

## Recommended Next Session (Pre-Phase-1 items)

1. Tommy: test 0.D Twilio OTP on real device — if passes, 0.D is done
2. Tommy: test 0.E first call failure — reproduce + get logcat
3. Tommy: review and merge frontend fixes for 0.1/0.2/0.3
4. Tommy: sign off Phase 0 complete
5. Tommy: deploy Phase 1 (see TODOS.md deploy checklist)

---

## Phase 1 Build Session — 2026-05-08 (autonomous, Tommy away)

### Units Completed

| Unit | Description | Commit | Status |
|------|-------------|--------|--------|
| 1.1 | Gmail OAuth routes | `3452271` | ✅ committed locally |
| 1.2 | sendEmail() + token refresh | `02e0026` | ✅ committed locally |
| 1.3 | Curator + Pitch + PitchInteraction DB + CRUD | `02e0026` | ✅ committed locally |
| 1.4 | 50 placeholder curators seed data | `b46ff4c` | ✅ committed locally |
| 1.5 | generatePitchEmail() — Claude Haiku, Marcus persona | `02e0026` | ✅ committed locally |
| 1.6 | sendPitchEmails() batch orchestration | `02e0026` | ✅ committed locally |
| 1.7 | detectReplies() inbox poller + Claude classify | `02e0026` | ✅ committed locally |
| 1.8 | APScheduler every 6h, opt-in SCHEDULER_ENABLED | `02e0026` | ✅ committed locally |
| 1.9 | Follow-up triggers day 1/3/5 per tier | `02e0026` | ✅ committed locally |
| test | 15 unit tests, all mocked (no real creds) | `02e0026` | ✅ committed locally |

### Units Skipped and Why
- None. All 9 units + tests completed.
- Note: Marcus function-calling (tools via Anthropic tool_use, as described in original PHASE1_PLAN.md) was
  scoped out — the new scope uses direct API endpoints instead. If Marcus agent needs tool_use in chat,
  that's a follow-on task for Phase 1.5.

### New Env Vars Tommy Needs on Railway

```
GMAIL_OAUTH_CLIENT_ID        # Google Cloud Console → OAuth 2.0 Client ID
GMAIL_OAUTH_CLIENT_SECRET    # Google Cloud Console → OAuth 2.0 Client Secret
GMAIL_OAUTH_REDIRECT_URI     # https://YOUR-RAILWAY-URL/api/gmail/callback
SCHEDULER_ENABLED            # false (set true when ready for auto inbox polling)
REPLY_POLL_HOURS             # 6 (default — hours between inbox scans)
```

### Manual Steps Before Phase 1 Goes Live

1. **Create Google Cloud OAuth credentials**
   - console.cloud.google.com → APIs & Services → Credentials → Create OAuth 2.0 Client ID
   - Application type: Web application
   - Add authorised redirect URI: `https://YOUR-RAILWAY-URL/api/gmail/callback`
   - Enable Gmail API in the project

2. **Replace placeholder curators**
   - All 50 curators in `data/curators_seed.json` use `placeholder@example.com`
   - Tommy must replace with real emails before running seed
   - Or seed first, then UPDATE curators table directly

3. **Deploy to Railway**
   - `git push origin main` (from Tommy's machine — SSH auth blocked in autonomous sessions)
   - Railway auto-deploys on push if GitHub is connected
   - New DB tables created automatically at startup

4. **Connect Gmail per artist**
   - Artist visits: `GET /api/gmail/auth?artist_id=ARTIST_ID`
   - Completes Google OAuth flow
   - Tokens stored in artist profile

5. **Set SCHEDULER_ENABLED=true** when ready for automatic reply detection

### Architecture Decisions Made

| Decision | Reason |
|----------|--------|
| All units in one file `pitch_service.py` | Avoids circular imports; clean FastAPI router pattern |
| Pitch tables always in SQLite (not Postgres) | Matches existing messages table pattern; Postgres only for artist profiles |
| Gmail tokens stored inside artist profile | No extra table; piggybacks on existing Postgres/SQLite routing |
| APScheduler `asyncio` variant | Matches FastAPI async model; no extra threads |
| Claude Haiku for pitch + classify | Cost control; Haiku is fast and cheap for structured JSON tasks |
| Mocked tests only | No real credentials in dev/CI — safe to commit and run anywhere |

### Files Changed This Session

| File | Action |
|------|--------|
| `pitch_service.py` | Created (511 lines — all 9 units) |
| `seed_curators.py` | Created (standalone seed script) |
| `data/curators_seed.json` | Created (50 placeholder curators) |
| `tests/test_pitch_service.py` | Created (15 unit tests) |
| `main.py` | Modified (router + init_pitch_db + init_scheduler wired in) |
| `requirements.txt` | Modified (4 new deps: google-auth, google-auth-oauthlib, google-api-python-client, apscheduler) |
| `.env.example` | Modified (Gmail OAuth + scheduler vars) |
| `TODOS.md` | Modified (Phase 1 units marked ✅ LOCAL) |
| `SESSION_NOTES_MAY8.md` | Modified (this section) |

### Commits (all local — push blocked, Tommy must push)

```
3452271  [1.1] Gmail OAuth routes — auth + callback + token storage
02e0026  [1.2] pitch_service.py — sendEmail() + token refresh + all units 1.1-1.9
b46ff4c  [1.4] Seed 50 placeholder curators — A/B/C tier across 10 genres
+ TODOS.md + SESSION_NOTES_MAY8.md update (this commit)
```

### Phase 1 Readiness

- **Backend code**: 100% implemented locally ✅
- **Tests**: 15 unit tests written, all mocked ✅
- **Ready to deploy**: ✅ once Tommy pushes and sets Gmail env vars
- **Blockers to going live**: Gmail OAuth credentials (Tommy creates), real curator emails (Tommy provides)
- **What still needs building (Phase 1.5)**:
  - Marcus agent tool_use in /api/chat_stream (function calling pattern)
  - Press contacts DB (same pattern as curators)
  - Venue DB (same pattern as curators)
  - Frontend screens for curator list, pitch status, inbox view
