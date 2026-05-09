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
| TODOS.md | Created | TBD |
| SESSION_NOTES_MAY8.md | Created | TBD |
| PHASE1_PLAN.md | Created | TBD |
| .gitignore | Updated (added docx) | TBD |

---

## Recommended Next Session

1. Tommy: test 0.D Twilio OTP on real device — if passes, 0.D is done
2. Tommy: test 0.E first call failure — reproduce + get logcat
3. Tommy: review and merge frontend fixes for 0.1/0.2/0.3
4. Tommy: sign off Phase 0 complete
5. Start Phase 1 Unit 1.1 — Gmail OAuth routes + token storage
