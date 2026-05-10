# PLMKR Cumulative Merge Verification — May 10, 2026

## Scope

22 branches (17 Tier 1+2 + 5 Tier 3) merged sequentially onto throwaway branches.
Full pytest suite run against the merged state after each tier.

---

## Branches merged (in order)

### Tier 1+2 (17 branches)
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
17. `docs/r31-cleanup`

### Tier 3 (5 branches)
18. `fix/r21-loud-migration-failures`
19. `fix/r06-postgres-failover-loud`
20. `fix/r22-422-passthrough`
21. `fix/r07-broader-crash-recovery`
22. `fix/r23-prompt-injection-v1-sanitization`

---

## V7 — Final result (GREEN)

```
204 passed in 89.97s (0:01:29)
```

**Verdict: GREEN — 204/204**

Throwaway branch `verify/cumulative-tier3` deleted after run.

---

## History

| Run | Result | Notes |
|-----|--------|-------|
| V1–V5 | (prior session) | |
| V6-YELLOW | 165/166 | `test_writable_dir_logs_ok` failed — capsys captured Twilio startup warning from module reload inside `_get_check_fn()`, polluting the capture window before `fn()` was called |
| V6-GREEN | **166/166** | One-line fix: `capsys.readouterr()` after `_get_check_fn()` but before `fn()` flushes startup noise from the capture window |
| V7-GREEN | **204/204** | 17 Tier 1+2 + 5 Tier 3 branches. 38 new tests from R-06/R-07/R-21/R-22/R-23. 7 manual conflict resolutions. |

---

## Fix applied (V6)

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

Seven branches required manual conflict resolution:

| Branch | File | Resolution |
|--------|------|------------|
| b03-daily-send-quota | tests/test_pitch_service.py | Kept both test blocks (idempotency + quota) |
| b05-stripe-webhook-signature | main.py | Kept Railway guard from HEAD; used `_verify_stripe_event()` from incoming |
| r01-dockerfile-service-files | Dockerfile | Kept `anthropic_utils.py` + `prompt_safety.py` (b01/r23) + all service files (r01) |
| r04-api-key-auth | main.py | Kept `ALLOWED_ORIGINS` block (b07) + added `_PLMKR_API_KEY` (r04) |
| r05-anthropic-graceful-degradation | admin_service.py | Kept `**_security_posture()` (r04) + added `anthropic_available` (r05) |
| r21-loud-migration-failures | social_service.py | Kept loud migration error (r21) + kept timezone migration block (f01) |
| r07-broader-crash-recovery | release_service.py | Kept C-03 reset comment (HEAD) + reset code (r07) |
