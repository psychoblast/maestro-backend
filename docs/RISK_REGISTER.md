# PLMKR — Risk Register
Last updated: 2026-05-10 (Session Tier 3 — Units 1–6)

Severity: 🔴 HIGH · 🟡 MEDIUM · 🔵 LOW/INFO
Status: Open · Mitigated (pending merge) · Closed

---

## R-06 — Postgres silent failover to SQLite

| Field | Value |
|-------|-------|
| Severity | 🔴 HIGH |
| File | main.py ~1060-1065 |
| Status | Mitigated — pending merge |
| Branch | fix/r06-postgres-failover-loud |

When DATABASE_URL is set but Postgres init fails, code silently sets DATABASE_URL="" and falls back to SQLite — data loss risk in production. Fix: fail loud (sys.exit) unless DB_FAILOVER_TO_SQLITE=true escape hatch is set.

---

## R-07 — Intermediate-state rows leak on crash

| Field | Value |
|-------|-------|
| Severity | 🟡 MEDIUM |
| File | release_service.py, all services |
| Status | Mitigated — pending merge |
| Branch | fix/r07-broader-crash-recovery |

C-03 fixed campaign_actions stuck-running rows. R-07 sweeps all tables for other intermediate-state leaks (sending, in_progress, processing, etc.) and adds reset queries in init functions where needed.

---

## R-21 — Silent migration failure (OperationalError swallowed)

| Field | Value |
|-------|-------|
| Severity | 🟡 MEDIUM |
| File | pitch_service.py ~110, social_service.py ~103 (+ sweep) |
| Status | Mitigated — pending merge |
| Branch | fix/r21-loud-migration-failures |

`except sqlite3.OperationalError: pass` swallows all DB migration errors. Only the "duplicate column name" case (idempotent re-run) should be silenced. All other errors must re-raise with a wrapped message so the app refuses to start.

---

## R-22 — FastAPI 422 responses intercepted by generic error handler

| Field | Value |
|-------|-------|
| Severity | 🟡 MEDIUM |
| File | main.py (exception_handler) |
| Status | Mitigated — pending merge |
| Branch | fix/r22-422-passthrough |

Generic `@app.exception_handler(Exception)` wraps all unhandled errors including FastAPI's native RequestValidationError (HTTP 422) — breaking frontend validation error handling. Fix: explicit handlers for RequestValidationError and HTTPException that preserve native format.

---

## R-23 — Prompt injection via curator/contact fields

| Field | Value |
|-------|-------|
| Severity | 🟡 MEDIUM |
| File | pitch_service.py ~669-675, pr_service.py, booking_service.py |
| Status | Mitigated — pending merge |
| Branch | fix/r23-prompt-injection-v1-sanitization |

Curator/contact fields (name, outlet, genres/beat/region) are interpolated directly into Anthropic prompts without sanitization. v1 mitigation: shared `prompt_safety.sanitize_for_prompt()` strips control characters, normalises whitespace, truncates to 200 chars. v2 (system/user separation) deferred.

---

## R-31 — Seed scripts missing from Dockerfile

| Field | Value |
|-------|-------|
| Severity | 🔵 LOW |
| File | Dockerfile |
| Status | **Closed** |
| Branch | fix/r01-dockerfile-service-files |
| Verified | 2026-05-10 |

`seed_curators.py`, `seed_pr_contacts.py`, `seed_booking_contacts.py` confirmed present in `fix/r01-dockerfile-service-files` Dockerfile COPY stanza. No additional change needed.

```
COPY pitch_service.py pr_service.py booking_service.py \
     social_service.py release_service.py admin_service.py \
     seed_curators.py seed_pr_contacts.py seed_booking_contacts.py ./
```
