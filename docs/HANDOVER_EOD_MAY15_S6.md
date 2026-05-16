# PLMKR EOD Handover — May 15, 2026 (Session 6, late evening)

## Done (verified)

### Unit 1 — Phase 1 State Audit (read-only)

Produced `docs/PHASE_1_AUDIT_MAY15.md`. All Phase 1 code was read and assessed.

**Findings summary:**

| Section | Status |
|---------|--------|
| A — Marcus agent (main.py + skill file + pitch system prompt) | ✅ COMPLETE |
| B — Curator data model (schema, CRUD helpers, seed JSON) | ✅ COMPLETE |
| C — Curator matching logic | 🟡 PARTIAL — compound-genre LIKE bug + no scoring |
| D — Pitch generation + followup logic | ✅ COMPLETE |
| E — Gmail OAuth (routes, refresh, send, inbox scan, classify) | ✅ COMPLETE |
| F — Test coverage (23 unit + 1 integration lifecycle) | 🟡 PARTIAL — inbox functions uncovered |

Phase 1 is ~85% production-ready. The two gaps identified are both buildable without
real credentials.

### Unit 2 — Gap closure: compound-genre fix + inbox intelligence tests

**Gap 1 fixed: `_db_list_curators` compound-genre LIKE bug**

Before: `genre="indie pop"` → `genres LIKE '%indie pop%'` → 0 results against
curators whose JSON genres are `["indie","pop"]`.

After: tokenised into `["indie","pop"]` → two LIKE clauses → correct match.

```python
tokens = [t.strip() for t in genre.replace(",", " ").split() if t.strip()]
for token in tokens:
    q += " AND genres LIKE ?";  params.append(f"%{token}%")
```

3 regression tests: compound match, no false positives, single-token still works.

**Gap 2 fixed: direct unit tests for `_classify_reply()` + `detect_replies()`**

Previously only covered by integration test. Added 10 direct unit tests:
- `_classify_reply()`: positive, negative, malformed JSON fallback, R-34 prompt-injection guard verified (delimiter present, "Ignore any instructions" present in wrapped content)
- `detect_replies()`: thread match → status=replied + inbound interaction, no-match path (status stays sent), empty inbox

Branch: `feat/phase1-audit-may15-s6-unit2-gap-closure`. Merged to main.

### Unit 3 — Seed scripts

`scripts/seed_curators.py`: loads `data/curators_seed.json` (50 curators), inserts idempotently, production guard (`RAILWAY_ENVIRONMENT=production` → exit 1).

`scripts/seed_test_pitch_data.py`: seeds 3 test artists, 3 curators, 4 pitches (draft/sent/replied), 2 interactions — all IDs prefixed `test-` for easy identification and purge. Same production guard.

`docs/SEED_DATA.md`: usage, schema, tier distribution, purge SQL, production guard explanation.

Branch: `feat/phase1-audit-may15-s6-unit3-seed-data`. Merged to main.

### Unit 4 — This handover

`docs/HANDOVER_EOD_MAY15_S6.md` (this file), `docs/TOMORROW_CHAT_HANDOVER.md` updated,
tag `v0.1-eod-2026-05-15-s6`.

---

## Verified

```
[ ] 374/374 tests GREEN (364 floor + 10 new Unit 2 tests)          ✅
[ ] compound-genre fix: indie pop → matches ["indie","pop"] curator  ✅
[ ] _classify_reply tests: positive/negative/fallback/injection guard ✅
[ ] detect_replies tests: thread match/no match/empty inbox           ✅
[ ] scripts/seed_curators.py runs clean on temp DB                   ✅
[ ] scripts/seed_test_pitch_data.py runs clean on temp DB            ✅
[ ] production guard: RAILWAY_ENVIRONMENT=production → exit 1        ✅
[ ] No uncommitted changes on main                                   ✅
[ ] Zero real external API calls this session                        ✅
```

---

## New risks found this session

None. Bug fixed (compound-genre LIKE) was a functional defect, not a new risk — it
was already identified in the audit as Section C gap. No new infrastructure or auth
surface introduced.

---

## Still open (unchanged from S5)

- **R-02**: Railway persistent volume not created (data lost on redeploy). Tommy must upgrade to Hobby ($5/mo) and create `/data` volume.
- **R-11**: `APP_BASE_URL` must be set in Railway Variables (code handles missing value correctly — hard-fail at boot). Tommy must set before any deploy.
- **R-16**: Gmail OAuth env vars not set on Railway — all pitch/PR/booking pipeline blocked.
- **R-17**: Valid `TWILIO_AUTH_TOKEN` not set on Railway (32-char hex format required).
- **R-24/R-25**: Require live Railway DB and Gmail account for smoke tests.
- **R-26**: Buffer real posting behind `BUFFER_LIVE=false` flag.
- **R-27**: Scheduler behind `SCHEDULER_ENABLED` flag.

---

## Phase 1 remaining work (for next session)

From the Unit 1 audit, the remaining Phase 1 gaps are:

1. **Curator scoring algorithm** (Section C, medium priority): `_db_list_curators` now tokenises correctly, but there is still no weighted scoring — no recency penalty for `last_pitched_at`, no multi-genre overlap weight. A scoring function would rank curators by match quality, not just tier+response_rate. This is a polish item, not blocking.

2. **`_generate_followup()` tests** (Section F): the follow-up generation function has no direct unit tests. Low priority — business logic is straightforward.

3. **Gmail OAuth callback full-flow test**: the callback route `_get_gmail_service` + token refresh path is not tested end-to-end. Blocking for live Gmail, but not for local testing.

4. **Phase 2 start** (PR outreach): pending Tommy confirming Phase 1 live deploy is working (R-02 + R-16 + R-11 resolved).

---

## Session metadata

- Branch naming: `feat/phase1-audit-may15-s6-unitN-<desc>`
- Merges to main: 3 (`--no-ff`)
- Tests before: 364 | Tests after: **374** | Delta: +10
- Risks closed: 0 (no new closures this session)
- New risks: 0
- Bugs fixed: 1 (compound-genre LIKE — no risk register entry, functional defect)
- Credentials touched: none
- External API calls made: **none** (all mocked via FastAPI TestClient)
