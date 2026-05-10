# PLMKR Cumulative Merge Verification — May 10, 2026

## Scope

16 fix branches merged sequentially onto a throwaway `verify/cumulative-final-2` branch.
Full pytest suite run against the merged state.

---

## Branches merged (in order)

1. `fix/b01-anthropic-retry`
2. `fix/b02-deterministic-idempotency`
3. `fix/b03-daily-send-quota`
4. `fix/b05-stripe-dev-flag-prod-guard`
5. `fix/b05-stripe-webhook-signature`
6. `fix/b06-upload-size-limit`
7. `fix/b07-cors-lockdown`
8. `fix/c03-startup-running-reset`
9. `fix/f01-per-artist-timezone`
10. `fix/r01-dockerfile-service-files`
11. `fix/r02-persistent-volume-staging`
12. `fix/r04-api-key-auth`
13. `fix/r04-health-reports-auth-status`
14. `fix/r05-anthropic-graceful-degradation`
15. `fix/r10-scheduler-backfill-protection`
16. `fix/r12-delete-send-test-email`

---

## V6 — Final result (GREEN)

```
166 passed in 98.49s (0:01:38)
```

**Verdict: GREEN — 166/166**

---

## History

| Run | Result | Notes |
|-----|--------|-------|
| V1–V5 | (prior session) | |
| V6-YELLOW | 165/166 | `test_writable_dir_logs_ok` failed — capsys captured Twilio startup warning from module reload inside `_get_check_fn()`, polluting the capture window before `fn()` was called |
| V6-GREEN | **166/166** | One-line fix: `capsys.readouterr()` after `_get_check_fn()` but before `fn()` flushes startup noise from the capture window |

---

## Fix applied

**Branch:** `fix/r02-persistent-volume-staging`
**Commit:** `db480bf — [test] R-02 — flush capsys before assertion to scope capture window`
**File:** `tests/test_r02_data_writable_check.py::test_writable_dir_logs_ok`

```python
fn = _get_check_fn(monkeypatch, tmp_path)
capsys.readouterr()   # flush startup prints from module reload

fn()

captured = capsys.readouterr()
```

**Isolated verification:** 3/3 pass on `fix/r02-persistent-volume-staging` alone.
**Cumulative verification:** 166/166 on `verify/cumulative-final-2` (branch deleted after run).

---

## Conflict resolutions (cumulative merge)

Five branches required manual conflict resolution:

| Branch | File | Resolution |
|--------|------|------------|
| b03-daily-send-quota | tests/test_pitch_service.py | Kept both test blocks (idempotency + quota) |
| b05-stripe-webhook-signature | main.py | Kept Railway guard from HEAD; used `_verify_stripe_event()` from incoming |
| r01-dockerfile-service-files | Dockerfile | Kept `anthropic_utils.py` (b01) + added all service files (r01) |
| r04-api-key-auth | main.py | Kept `ALLOWED_ORIGINS` block (b07) + added `_PLMKR_API_KEY` (r04) |
| r05-anthropic-graceful-degradation | admin_service.py | Kept `**_security_posture()` (r04) + added `anthropic_available` (r05) |
