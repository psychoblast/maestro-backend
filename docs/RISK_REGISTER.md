# PLMKR Risk Register

Last updated: 2026-05-10

---

## R-06 — Silent Postgres failover masks DB boot failure

**Severity:** High  
**Status:** Mitigated — pending merge  
**Branch:** `fix/r06-postgres-failover-loud` (commit `b35498c`)  
**Description:** If Postgres init fails, the app silently falls back to SQLite in production. Artists lose all data written after deploy without any alert.  
**Fix:** `_init_pg_connection()` in `main.py` calls `sys.exit(1)` on Postgres failure unless `DB_FAILOVER_TO_SQLITE=true` is explicitly set. 6 tests cover all branches.

---

## R-07 — Intermediate-state leak on crash during campaign action execution

**Severity:** Medium  
**Status:** Mitigated — pending merge  
**Branch:** `fix/r07-broader-crash-recovery` (commit `b40f666`)  
**Description:** `campaign_actions` rows are set to `status='running'` before the async action executes. If the app crashes mid-execution, rows are stuck `running` forever and never retried.  
**Fix:** `init_release_db()` now resets all `running` rows to `pending` at startup (C-03 pattern). Sweep confirmed `campaign_actions` is the only table with this pattern. 4 tests.

---

## R-21 — Silent SQLite migration failures hide schema corruption

**Severity:** High  
**Status:** Mitigated — pending merge  
**Branch:** `fix/r21-loud-migration-failures` (commit `56540c5`)  
**Description:** `ALTER TABLE ADD COLUMN` migrations in pitch/pr/booking/social services catch all `sqlite3.OperationalError` silently. A real schema error (disk full, locked DB, wrong table name) would be swallowed.  
**Fix:** Re-raise any `OperationalError` that does NOT contain "duplicate column name". 12 tests.

---

## R-22 — 422 and HTTPException responses missing request_id

**Severity:** Low  
**Status:** Mitigated — pending merge  
**Branch:** `fix/r22-422-passthrough` (commit `358f8ab`)  
**Description:** The generic `Exception` handler in `main.py` includes `request_id` for traceability, but FastAPI's native 422 and HTTPException responses bypass it, making those error responses untraceable in logs.  
**Fix:** Explicit `@app.exception_handler(RequestValidationError)` and `@app.exception_handler(HTTPException)` handlers added to `main.py`, each injecting a `request_id`. 5 tests.

---

## R-23 — User-controlled strings interpolated raw into LLM prompts

**Severity:** High  
**Status:** Mitigated — pending merge  
**Branch:** `fix/r23-prompt-injection-v1-sanitization` (commit `90aa094`)  
**Description:** Artist names, bios, curator/contact names, and other user-controlled fields are interpolated directly into Claude prompts in pitch/pr/booking services. A malicious or misconfigured value with newlines can inject new instructions into the prompt.  
**Fix:** `prompt_safety.py` introduces `sanitize_for_prompt(value, max_len=200)` which strips newlines, carriage returns, and control chars, collapsing to single spaces. Applied to all user-controlled fields at the 3 prompt construction sites. 11 tests.

---

## R-31 — Dockerfile seed scripts missing

**Severity:** Low  
**Status:** Closed  
**Branch:** `docs/r31-cleanup` (audit finding — documentation only)  
**Description:** Audit AU-2 flagged that seed scripts were referenced in docs but not confirmed present in Dockerfile.  
**Resolution:** Confirmed seed scripts exist and are correctly wired in Dockerfile. RISK_REGISTER.md entry created to close the finding.
