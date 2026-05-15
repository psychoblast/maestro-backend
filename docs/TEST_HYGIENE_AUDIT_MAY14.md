# Test Suite Hygiene Audit — 2026-05-14

**Auditor:** Claude (autonomous batch session #2)
**Suite state:** main @ `70e89b9` — 225 tests collected
**Scope:** `tests/` tree (37 files: 30 unit, 7 integration)

---

## Checklist Results

| Check | Result | Notes |
|-------|--------|-------|
| `@pytest.mark.skip` without explanation | **PASS** | None found |
| `@pytest.mark.xfail` without explanation | **PASS** | None found |
| Duplicate test names across files | **PASS** | None found |
| Duplicate test names within a file | **PASS** | None found |
| `print()` calls in test bodies | **PASS** | None found |
| `sys.path` hacks | **PASS** | None found |
| `sleep()` > 1 s | **PASS** | One `asyncio.sleep(0.05)` — see note |
| Shared filesystem without cleanup | **PASS** | All DB tests use `tmp_path` |
| `assert True` / `assert 1==1` trivials | **PASS** | None found |

**Overall: CLEAN.** No issues require action.

---

## Notes

### asyncio.sleep(0.05) in test_r33_async_anthropic_retry.py:119

The 50 ms sleep is intentional concurrency instrumentation. The test (`test_r33_concurrency_fast_task_runs_during_retry`) spins a "fast task" alongside the retry helper to confirm the event loop is not blocked. The sleep is the fast task itself — not a polling timeout. It is well under 1 s and necessary for the test's validity.

### "Must Not Raise" Tests (no explicit `assert` statement)

The following tests verify correct behaviour by confirming no exception is raised. This is an idiomatic pytest pattern — no assert statement is needed because any exception would fail the test:

| File | Test | What it verifies |
|------|------|-----------------|
| `test_pitch_service.py:328` | `test_quota_allows_first_batch` | quota under limit → no 429 |
| `test_pitch_service.py:354` | `test_quota_separate_per_artist` | independent per-artist counters |
| `test_f01_per_artist_timezone.py:72` | `test_migration_idempotent` | `init_social_db()` safe to call twice |
| `test_r21_loud_migration_failures.py:79` | `test_pitch_migration_swallows_duplicate_column` | duplicate-column error swallowed |
| `test_r21_loud_migration_failures.py:91` | `test_pitch_migration_idempotent` | second `init_pitch_db()` call safe |
| `test_r21_loud_migration_failures.py:115` | `test_social_migration_swallows_duplicate_column` | same for social table |
| `test_r21_loud_migration_failures.py:125` | `test_social_migration_idempotent` | second `init_social_db()` call safe |
| `test_r21_loud_migration_failures.py:149` | `test_pr_migration_swallows_duplicate_column` | same for PR table |
| `test_r21_loud_migration_failures.py:161` | `test_pr_migration_idempotent` | second `init_pr_db()` call safe |
| `test_r21_loud_migration_failures.py:185` | `test_booking_migration_swallows_duplicate_column` | same for booking table |
| `test_r21_loud_migration_failures.py:197` | `test_booking_migration_idempotent` | second `init_booking_db()` call safe |

These are all intentional and correctly structured. No changes required.

Similarly, tests using `mock.assert_called_once_with()` and `mock.assert_not_called()` (e.g. `test_anthropic_utils.py:134`, `test_stripe_webhook.py:168`) assert via the Mock API rather than the `assert` keyword — equally valid.

---

## Recommendation

No hygiene issues found. Suite is well-structured:
- Isolation: every test that touches SQLite uses `tmp_path` or `monkeypatch`
- Markers: none skipped or expected-to-fail without reason
- No sleeping, no sys.path abuse, no debug prints left in
- Test names are unique across the entire suite

Next review recommended after the suite crosses 300 tests.
