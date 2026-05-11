# Session Report — 2026-05-10 (Tier 1 Risk Mitigations)

## Summary

Branch strategy: one `fix/` branch per unit, all from `main` — no cross-branch dependencies.
Session type: Autonomous (user stepped away after approving Units 1–4, autonomous for Units 5–10).

---

## Commits This Session

**Total: 10 commits across 9 fix branches + 1 docs branch**

```
1347e25  fix/b07-cors-lockdown             [B-07] CORS lockdown — env-driven origin list
742b743  fix/r04-api-key-auth              [R-04] X-API-Key auth middleware
03ed9b5  fix/b03-daily-send-quota          [B-03] Per-artist daily send quota (50/day)
05edb34  fix/b06-upload-size-limit         [B-06] Upload size limit + extension allowlist
cc60c89  fix/b02-deterministic-idempotency [fix] B-02 — deterministic idempotency keys
77819b3  fix/b01-anthropic-retry           [fix] B-01 — shared Anthropic retry helper
5d7272e  fix/c03-startup-running-reset     [fix] C-03 — reset stuck running campaign actions
c8b4aad  fix/b05-stripe-webhook-signature  [fix] B-05 — Stripe webhook signature enforcement
45318b0  fix/r01-dockerfile-service-files  [fix] R-01 — add missing COPY for service files
8c2e20f  docs/risk-register                [docs] R-23 correction — fabricated notes field
```

---

## Unit Status

| Unit | Risk ID | Description | Branch | Status | Tests |
|------|---------|-------------|--------|--------|-------|
| 1 | R-23 | Docs correction: fabricated `notes` field in prompt-injection code snippet | `docs/risk-register` | ✅ Done | — |
| 2 | R-01 | Dockerfile: add COPY for all 6 service files + 3 seed scripts | `fix/r01-dockerfile-service-files` | ✅ Done | — |
| 3 | B-05 | Stripe webhook: enforce signature; env-gated dev bypass | `fix/b05-stripe-webhook-signature` | ✅ Done | 5 |
| 4 | C-03 | Reset `campaign_actions` stuck in `status='running'` at startup | `fix/c03-startup-running-reset` | ✅ Done | 1 |
| 5 | R-13 | Anthropic retry: `_anthropic_call_with_retry()`, 4 attempts, 1/2/4s backoff | `fix/b01-anthropic-retry` | ✅ Done | 9 |
| 6 | R-08 | Deterministic idempotency keys: `sha256(artist_id:contact_id:YYYY-MM-DD)` | `fix/b02-deterministic-idempotency` | ✅ Done | 2 |
| 7 | R-14 | `/api/transcribe` upload size limit (25 MB default) + extension allowlist | `fix/b06-upload-size-limit` | ✅ Done | 13 |
| 8 | R-09 | Per-artist daily send quota: SQLite-backed, 50/day, `DAILY_PITCH_QUOTA` env | `fix/b03-daily-send-quota` | ✅ Done | 5 |
| 9 | R-03 | X-API-Key middleware: `PLMKR_API_KEY` env, dev-permissive if unset, skip `/health` | `fix/r04-api-key-auth` | ✅ Done | 8 |
| 10 | R-15 | CORS lockdown: env-driven `ALLOWED_ORIGINS`, no wildcard | `fix/b07-cors-lockdown` | ✅ Done | 8 |

---

## New Tests Added

| Suite | New tests | All passing |
|-------|-----------|-------------|
| tests/test_stripe_webhook.py (new) | 5 | ✅ |
| tests/test_release_service.py (added 1) | +1 | ✅ |
| tests/test_anthropic_utils.py (new) | 9 | ✅ |
| tests/test_pitch_service.py (added 7) | +7 | ✅ |
| tests/test_transcribe.py (new) | 13 | ✅ |
| tests/test_api_key_auth.py (new) | 8 | ✅ |
| tests/test_cors.py (new) | 8 | ✅ |
| **Total new tests** | **51** | ✅ |

---

## Estimated API Spend

~$0.00 — zero real Anthropic API calls made this session. All tests mock the client.
No Railway deploys performed. No external API calls.

---

## Technical Decisions Made

1. **anthropic_utils.py as shared module** — rather than duplicating retry logic in all 4 services, extracted to a shared `anthropic_utils.py`. Trade-off: adds one more `COPY` line to Dockerfile (trivial merge conflict with R-01 branch).

2. **Quota table in pitch_service** — `daily_send_quota` table lives in the pitch service DB schema since all 3 batch handlers already import from `pitch_service` (for `send_email`, `GmailNotConnected`). PR and booking services do lazy imports at call time to avoid circular imports at module load.

3. **Middleware for API key, not dependency injection** — using `BaseHTTPMiddleware` instead of a FastAPI `Depends()` makes it easier to whitelist paths (skip `/health`, `/docs`). Dependency injection would require modifying every router individually.

4. **CORS default includes Railway + Vercel + localhost** — explicit whitelist over wildcard. The `ALLOWED_ORIGINS` env var completely replaces the defaults when set (no additive logic) to avoid confusion about what's actually allowed.

5. **No-extension filenames fall back to `.m4a`** — a file uploaded with no extension (common from mobile recorders) is treated as `.m4a` rather than rejected. This matches the pre-existing fallback behavior in the `ext = ... or ".m4a"` line.

---

## What Was NOT Done (Explicit Exclusions)

- R-02: `/data` ephemeral storage → requires infra decision (Railway volume vs. external DB)
- R-05: `ANTHROPIC_API_KEY` hard-crash at boot → graceful degradation pattern
- R-10: Scheduler backfill bulk-fire → APScheduler `coalesce=True` + `misfire_grace_time`
- R-12: `/send-test-email` unauthenticated → partially addressed by R-03 (API key auth) once merged

---

## Next Session

1. Merge all 9 `fix/` branches to main via PR review
2. Railway redeploy — verify R-01 fix resolves the dark-service issue
3. `curl /api/admin/health/deep` on live Railway — confirm all service modules loaded
4. R-02 decision: persistent storage strategy
5. R-05: startup degradation guard
