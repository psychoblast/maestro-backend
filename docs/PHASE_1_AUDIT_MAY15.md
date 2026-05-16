# PLMKR — Phase 1 State Audit (May 15, 2026, Session 6)

Read-only investigation. No code changes. Branch: none (main only).

---

## Summary

Phase 1 was built across May 8-9 sessions. The core is **substantially complete** — 52 KB of
production code in `pitch_service.py`, 23 unit tests, and a full integration lifecycle test.
Two gaps remain: **curator matching quality** (compound-genre LIKE bug, no scoring) and
**thin test coverage on inbox intelligence** (detect_replies, _classify_reply untested directly).

| Section | Area | Status |
|---------|------|--------|
| A | Marcus agent | ✅ COMPLETE |
| B | Curator data model | ✅ COMPLETE |
| C | Curator matching logic | 🟡 PARTIAL — genre match broken for compound genres |
| D | Pitch generation | ✅ COMPLETE |
| E | Gmail OAuth | ✅ COMPLETE |
| F | Test coverage | 🟡 PARTIAL — inbox intelligence uncovered |

---

## (A) Marcus Agent

**Status: ✅ COMPLETE**

Marcus is fully wired end-to-end.

- **main.py ~L89**: agent record `{"id": "puppet-master", "name": "Marcus", "title": "Artist Manager", "voice": "am_onyx", ...}` — registered in the global agent list, participates in handoff routing
- **main.py ~L162**: 5 greeting variants for Marcus
- **skills/maestro-puppet-master/SKILL.md**: comprehensive Marcus persona — 10 management laws, response protocols for deals/royalties/strategy/grants, global scope (LOCAL / NATIONAL / INTERNATIONAL layers), escalation and routing logic
- **pitch_service.py L710-724**: `_PITCH_SYSTEM` prompt — "You are Marcus, Artist Manager at Playmaker..." — used for pitch generation via Claude Haiku
- **static/agents/marcus.svg**, **static/agents/marcus.jpg**: both present
- **data/artists/marcus_dre_1773796428317.json**: sample artist profile

No gaps. Marcus persona is consistent between the skill file, the greeting variants, and the pitch system prompt.

---

## (B) Curator Data Model

**Status: ✅ COMPLETE**

All tables, all CRUD helpers, seed data.

**Tables (init_pitch_db(), pitch_service.py L58-131):**
- `curators`: id, name, outlet, genres (JSON TEXT), tier, contact_email, notes, last_pitched_at, response_rate, created_at
- `pitches`: id, artist_id, curator_id, status, subject, body, sent_at, replied_at, gmail_msg_id, gmail_thread_id, idempotency_key (UNIQUE), created_at
- `pitch_interactions`: id, pitch_id, direction, content, sentiment, ts
- `daily_send_quota`: artist_id, date, count — PRIMARY KEY (artist_id, date)
- `artists`: artist_id, data (JSON blob), updated_at

**CRUD helpers (all present):** `_db_upsert_curator`, `_db_get_curator`, `_db_list_curators`, `_db_create_pitch`, `_db_get_pitch`, `_db_update_pitch`, `_db_list_pitches`, `_db_add_interaction`, `_db_list_interactions`

**Seed data:** `data/curators_seed.json` — 50 records, fields: id, name, outlet, genres (list), tier (A/B/C), contact_email, notes, response_rate. Correct schema, realistic data (Spotify Editorial, blog outlets, indie playlist channels across A/B/C tiers).

No gaps.

---

## (C) Curator Matching Logic

**Status: 🟡 PARTIAL — compound-genre LIKE bug + no scoring algorithm**

### What exists

`_db_list_curators(genre, tier)` at pitch_service.py L482:
```python
if genre:
    q += " AND genres LIKE ?";  params.append(f"%{genre}%")
q += " ORDER BY tier ASC, response_rate DESC"
```

`send_pitch_emails` receives an explicit `curator_ids` list from the caller — the API does not auto-select curators. `api_generate_pitch` uses a single `curator_id`. The `_db_list_curators` function is only used internally and via `GET /api/curators?genre=X&tier=Y` (the list endpoint).

### Bug: compound-genre LIKE fails on JSON storage

genres are stored as a JSON array, e.g. `["indie", "pop"]` → stored string `'["indie","pop"]'`.

A query for `genre="indie pop"` produces:
```sql
WHERE genres LIKE '%indie pop%'
```
The substring "indie pop" does not appear in `'["indie","pop"]'` → **zero results**.

A query for `genre="indie"` works: `%indie%` matches `'["indie","pop"]'` → correct.

Any artist whose genre is a compound string (e.g. "indie pop", "r&b", "hip hop") will get zero curators returned, even if perfectly matched curators exist. This is a real functional defect.

### Missing: scoring algorithm

The current ordering (`ORDER BY tier ASC, response_rate DESC`) is rudimentary ranking but not genre-overlap scoring. There is no:
- Multi-token genre decomposition ("indie pop" → ["indie", "pop"])
- Per-genre match weight (exact genre match > partial)
- Recency penalty for `last_pitched_at` (curator pitched 3 days ago should rank lower)
- Composite score function

**Impact:** For the batch send endpoint (`/api/pitches/batch`), curator selection is caller-controlled — the client must know which `curator_ids` to pass. The matching gap only affects the list/filter endpoint used for discovery. This is less critical than the LIKE bug.

### Top gap to close (Unit 2)

Fix the compound-genre LIKE bug: tokenise the artist genre string and build multi-token OR conditions against the JSON array. This unblocks real curator discovery for any compound genre.

---

## (D) Pitch Generation

**Status: ✅ COMPLETE**

- **generate_pitch_email(artist, track_metadata, curator)** at pitch_service.py L736: calls Claude Haiku, full Marcus persona (`_PITCH_SYSTEM`), structured prompt with artist + curator + track context, returns `{subject, body, suggested_followup_days}`
- **_FOLLOWUP_SYSTEM**: Marcus follow-up prompt (2-3 sentences, reference original pitch)
- **_TIER_FOLLOWUP_DAYS**: `{"A": [1,3,5], "B": [3,5,7], "C": [5,7,10]}`
- **_get_pitches_needing_followup()** at L1177: queries sent+unreplied pitches, checks days-since-sent against tier thresholds
- **_generate_followup()** at L1217: Claude Haiku follow-up generation, same retry wrapper
- **R-34 guard in _classify_reply()**: delimited prompt prevents prompt injection from curator reply content

No gaps.

---

## (E) Gmail OAuth

**Status: ✅ COMPLETE**

Full OAuth 2.0 flow, token persistence, refresh, send, inbox scan, and reply classification.

**Routes:**
- `GET /api/pitches/gmail/auth?artist_id=X` — redirect to Google consent
- `GET /api/pitches/gmail/callback` — exchange code, save tokens
- `GET /api/pitches/gmail/status?artist_id=X` — `{connected: bool}`

**Internal:**
- `_get_gmail_service(artist_id)` at L282: loads tokens, refreshes if expired, builds `googleapiclient` service object
- `send_email(artist_id, to, subject, body)` at L410: Gmail API `users().messages().send()`
- `detect_replies(artist_id)` at L935: scans Gmail INBOX for messages in known thread IDs, matches to sent pitches
- `_classify_reply(content)` at L1040: Claude Haiku, R-34 delimited guard, returns `{sentiment, summary}`
- `_GmailStats` + `get_gmail_stats()` at L325: per-artist call counters, observable via `/api/admin/diagnostics/gmail-stats`

**Env vars required (not set on Railway — R-16):**
`GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`, `GMAIL_OAUTH_REDIRECT_URI`

No code gaps. Blocked only by Tommy setting R-16 env vars on Railway.

---

## (F) Test Coverage

**Status: 🟡 PARTIAL — inbox intelligence functions uncovered**

### Unit tests: tests/test_pitch_service.py (23 tests)

All mocked. No real credentials needed.

| Test group | Tests | What's covered |
|-----------|-------|---------------|
| 1.1 Gmail OAuth tokens | 3 | gmail_status (no tokens, with tokens), save/load tokens |
| 1.2 sendEmail | 2 | no-tokens raises GmailNotConnected, calls Gmail API + returns message_id |
| 1.3 Curator CRUD | 3 | create+get, list filter by tier, list filter by genre |
| 1.3 Pitch CRUD | 3 | create+get, update status, list by artist |
| 1.4 Interactions | 1 | add + list |
| 1.5 generatePitchEmail | 1 | returns {subject, body, suggested_followup_days} shape |
| 1.6 batch send | 1 | GmailNotConnected path (all fail gracefully) |
| 1.9 follow-up thresholds | 2 | no pitches → empty, recent pitch not triggered |
| Idempotency key | 2 | same key blocks second insert, different day allows second |
| 1.10 Daily quota | 5 | allows first batch, raises 429 when exceeded, accumulates, per-artist isolation, env override |

### Integration test: tests/integration/test_pitch_lifecycle.py (1 test, 6 assertions)

Full lifecycle: create curator → generate pitch (Claude mocked) → batch send (Gmail mocked) → verify status=sent + thread_id → inbox scan (Gmail mocked + Claude classify mocked) → verify status=replied + inbound interaction logged.

### Not covered

- `detect_replies()` — no direct unit test for the Gmail scan logic
- `_classify_reply()` — no direct unit test (covered only indirectly via integration test)
- `_generate_followup()` — no test at all
- `_poll_all()` — scheduler job, no test
- Curator list API endpoint (`GET /api/curators`) — no test
- response_rate update logic (L1068: `_db_upsert_curator({...response_rate...})`) — no test
- Compound genre LIKE bug — no test that would catch it (existing genre tests use single-word genres)

### Second gap to close (Unit 2)

Add direct unit tests for `detect_replies()` (empty inbox, one match, no match) and `_classify_reply()` (positive/negative/neutral, prompt-injection guard). These are the highest-stakes functions with zero direct coverage.

---

## Gaps ranked for Unit 2

1. **Compound-genre LIKE bug (Section C)** — `_db_list_curators` returns zero results for any compound artist genre (e.g. "indie pop", "hip hop"). Fix: tokenise genre string, build multi-term OR LIKE conditions. Add regression tests. This unblocks curator discovery for the majority of real artists.

2. **detect_replies + _classify_reply unit tests (Section F)** — core inbox intelligence with no direct unit tests. Mocked Gmail service + mocked Claude classify call. 4-6 tests covering happy path (thread matched → status=replied), no-match path, and _classify_reply prompt-injection guard.

---

## Files read during audit

- `main.py` (Marcus agent definition, greetings, handoff)
- `pitch_service.py` (full, 52 KB)
- `tests/test_pitch_service.py` (full, 377 lines)
- `tests/integration/test_pitch_lifecycle.py` (full)
- `skills/maestro-puppet-master/SKILL.md` (first 60 lines)
- `data/curators_seed.json` (record count + sample)
- `tests/integration/` directory listing
