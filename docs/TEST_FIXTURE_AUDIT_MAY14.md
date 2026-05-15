# PLMKR — Test Fixture Audit (May 14, 2026)

**Task:** C1 — Test fixture audit + dynamic dates  
**Branch:** `chore/test-fixture-audit`  
**Grep scope:** `tests/**/*.py` — all occurrences of `202X-MM-DD` patterns

---

## Findings Summary

| File | Line | Date | Classification | Action |
|------|------|------|----------------|--------|
| `tests/test_pitch_service.py` | 267 | `2026-05-08T10:00:00` | **Maintenance landmine** | Fixed |
| `tests/test_reports.py` | 39–40 | `2026-05-04` / `2026-05-10` | Intentional regression fixture | No change |
| `tests/test_reports.py` | 97 | `2026-05-07T10:00:00` | Intentional fixture (within window) | No change |
| `tests/integration/test_weekly_report.py` | 20–21 | `2026-05-04` / `2026-05-10` | Intentional regression fixture | No change |
| `tests/integration/test_weekly_report.py` | 62–95 | Various May 2026 | Intentional (within fixed window) | No change |
| `tests/integration/test_social_lifecycle.py` | 86, 135 | `2026-05-15` | Intentional fixture (not time-compared) | No change |
| `tests/test_release_service.py` | 213, 219 | `2026-06-01`, `2026-05-01` | Intentional fixture (no time comparison) | No change |
| `tests/test_r23_prompt_injection_sanitization.py` | 278 | `2026-06-01`, `2026-07-01` | Intentional domain data (injection test) | No change |
| `tests/test_booking_service.py` | 154 | `2026-08-15` | Intentional domain data (generate email) | No change |
| `tests/test_social_service.py` | 80 | `2026-05-09T18:00:00` | Intentional fixture (stored, not compared) | No change |
| `tests/test_admin_service.py` | 29–41 | `2026-01-01T00:00:00` | Schema DEFAULT (not time-compared) | No change |
| `tests/test_pitch_service.py` | 309–310 | `2026-05-10`, `2026-05-11` | Intentional regression (two-day hash test) | No change |
| `tests/test_f01_per_artist_timezone.py` | 97–113 | `2026-05-10` | Pinned via monkeypatch — intentional | No change |
| `tests/test_r07_broader_crash_recovery.py` | 46 | `2026-01-01T00:00:00` | Historical default value — intentional | No change |
| `tests/test_anthropic_utils.py` | 138 | `2024-07-31` | API header value — not a date fixture | No change |

---

## Fix Applied

### `tests/test_pitch_service.py` line 267 — naive datetime silently skipped

**Root cause:**  
`_get_pitches_needing_followup()` in `pitch_service.py` computes:
```python
ref = datetime.fromisoformat(ref_str.replace("Z", "+00:00"))
days = (now - ref).days   # now is timezone-aware
```
When `sent_at = "2026-05-08T10:00:00"` (no `+00:00`), `fromisoformat` returns a **naive** datetime. Subtracting naive from aware raises `TypeError`, which is caught by the surrounding `except Exception: continue`. The pitch is silently skipped — never appears in results — so the assertion passes, but the business logic being tested (days=0 not in tier threshold) is never exercised.

**Why it matters:**  
Any date where `days in tier_thresholds` would also be silently skipped. The test was a false positive — it would pass even if the threshold logic were completely broken.

**Fix:**  
Changed `now_str` from a hardcoded naive string to `datetime.now(timezone.utc).isoformat()` so the subtraction succeeds, `days=0`, and the assertion tests the actual threshold logic (0 is not in [3, 5, 7] for tier B).

---

## Classification Criteria

**Maintenance landmine:** Date is compared to real `datetime.now()` inside the code under test, causing the assertion to depend on when the test runs. Breaks when the date drifts into a threshold window.

**Intentional regression fixture:** Date is passed explicitly as a parameter to the function under test (e.g., `_aggregate_week_data(artist, WEEK_START, WEEK_END)`). The code never compares to real time — it operates on the provided window. Safe forever.

**Intentional domain data:** Date appears as field content (e.g., `available_dates: ["2026-08-15"]`) sent to a function whose output is a generated email. The exact date value doesn't affect the assertion.
