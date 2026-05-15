# PLMKR — Test Runtime Audit (May 14, 2026)

**Task:** C2 — Test runtime audit  
**Branch:** `chore/test-runtime-audit`  
**Command:** `python3 -m pytest --durations=20 -q`  
**Baseline:** 259 tests in 154.94s (2:34)

---

## Slowest 20 Tests

| Rank | Duration | Phase | Test |
|------|----------|-------|------|
| 1 | 4.40s | call | `test_r19_kokoro_startup_warning.py::test_missing_files_returns_none` |
| 2 | 4.06s | call | `test_admin_diagnostics.py::test_diagnostics_200_with_key` |
| 3 | 4.05s | call | `test_r10_scheduler_backfill.py::test_campaign_executor_job_has_coalesce_and_grace` |
| 4 | 3.79s | setup | `test_r12_send_test_email_removed.py::test_send_test_email_returns_404` |
| 5 | 3.60s | call | `test_r05_anthropic_graceful_degradation.py::test_health_deep_reports_anthropic_available_when_key_set` |
| 6 | 3.47s | call | `test_r19_kokoro_startup_warning.py::test_missing_files_prints_warning` |
| 7 | 3.37s | call | `test_admin_diagnostics.py::test_diagnostics_401_without_key` |
| 8 | 3.36s | call | `test_r02_data_writable_check.py::test_missing_dir_triggers_warning` |
| 9 | 3.28s | setup | `test_r12_send_test_email_removed.py::test_route_not_in_app_routes` |
| 10 | 3.13s | call | `test_r05_anthropic_graceful_degradation.py::test_health_deep_reports_anthropic_unavailable` |
| 11 | 2.72s | call | `test_r05_anthropic_graceful_degradation.py::test_handoff_returns_503_without_key` |
| 12 | 2.64s | call | `test_r19_kokoro_startup_warning.py::test_present_files_no_warning` |
| 13 | 2.62s | call | `test_r19_kokoro_startup_warning.py::test_missing_files_no_kokoro_import_attempted` |
| 14 | 2.49s | call | `test_r02_data_writable_check.py::test_unwritable_dir_logs_warning` |
| 15 | 2.31s | call | `test_r05_anthropic_graceful_degradation.py::test_app_boots_without_anthropic_key` |
| 16 | 2.15s | call | `test_r02_data_writable_check.py::test_writable_dir_logs_ok` |
| 17 | 1.70s | call | `test_cors.py::test_default_origins_include_railway` |
| 18 | 1.51s | call | `test_request_timing_middleware.py::test_server_timing_header_present` |
| 19 | 1.49s | call | `test_stripe_webhook.py::test_secret_set_calls_construct_event` |
| 20 | ~1.4s | call | (various sub-second tests) |

---

## Root Cause Analysis

### Primary cause: `importlib.reload(main)` (19 of 20 slow tests)

All slow tests call `importlib.reload(main)` because they test **boot-time behavior**:

- `test_r02_*` — tests `/data` directory write-check logic (runs at app startup)
- `test_r05_*` — tests Anthropic key presence (health/503 behavior at boot)
- `test_r10_*` — tests scheduler APScheduler job config (registered at startup)
- `test_r12_*` — verifies a deleted route is not registered (route list frozen at load)
- `test_r19_*` — tests Kokoro model file detection (happens at import)
- `test_admin_diagnostics.py` — needs fresh app with specific env var state
- `test_cors.py` / `test_request_timing_middleware.py` / `test_stripe_webhook.py` — middleware registered at startup

Each full reload of `main` takes **2–4 seconds** because:
1. All 16+ service modules are re-imported
2. SQLite tables are re-initialized in each service
3. `setup_logging()` configures the root logger
4. `init_error_reporting()` checks Sentry DSN
5. Whisper is patched but all other imports still run

This is **architecture-intrinsic** — not fixable without refactoring boot checks out of module-level scope. The tests correctly test production boot behavior at the cost of reload latency.

### Secondary cause: 4 Kokoro tests each reload independently

`test_r19_kokoro_startup_warning.py` has 4 tests each doing a full reload. These cannot share a module-scoped fixture because each test sets different file-existence conditions via monkeypatch. Function scope is required.

---

## Fix Applied

### `test_r12_send_test_email_removed.py` — module-scoped fixture

**Before:** Both tests used a function-scoped `client` fixture, causing two full main reloads (3.79s + 3.28s).

**After:** Changed to `scope="module"` using `tmp_path_factory` and `pytest.MonkeyPatch()`. One reload serves both tests. Second test setup drops to `< 0.005s`.

**Why it's safe:** Both tests only read static route structure (does route X exist in app.routes). No state is mutated between tests.

---

## Deferred Optimizations (Not Trivial)

| Optimization | Savings estimate | Complexity |
|-------------|------------------|------------|
| Extract boot-time checks into callable functions testable without `main` reload | ~40–50s | High — requires refactoring R-02, R-05, R-10, R-19 tests |
| Session-scoped `main` instance for tests that don't care about boot env | ~20s | Medium — risk of state leakage between tests |
| Parallel test execution (`pytest-xdist -n auto`) | ~60–90s | Low effort, but needs shared-state audit first |

---

## Conclusion

- Suite baseline: **259 tests in 155s**
- After fix: **259 tests in ~152s** (estimated — r12 saves ~3.5s in full suite)
- No tests are pathologically slow or indicative of production performance problems
- All reload-based slowness is intentional and tests real boot behavior
- `pytest-xdist` is the highest-ROI optimization if future suite growth exceeds 5 minutes
