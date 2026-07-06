# Audit Cleanup Batch — Completion Report

Source spec: `_audit/03_tech_debt.md` (units U1–U6). Branch: `fix/audit-cleanup-batch`.
Merged to `main` fast-forward-only. All work verified against the full chunked
test suite (216 files, 8/chunk, reconciled vs `pytest --collect-only`).

## STEP-0 ANOMALY FINDING — U1

**U1 fix PRESENT in commit `d2e0909`** ("fix: max_award is a true ceiling in
search_grant_programs; schema wording corrected; direction locked by tests",
authored 2026-07-04, branch `fix/jade-max-award-ceiling`, ancestor of HEAD /
merged to main before `e7b6850`).

There is no `[FIX-U1]` commit on this batch branch because U1 was already fixed
and merged in a prior session. Verified state on the merged branch:
- `fund_phantom_service.py:83,111` — docstring + inline comment both state
  `max_award` is a **CEILING**; a grant is excluded only when its `amount_min`
  is known and exceeds the ceiling (unknown `amount_min` never dropped).
- Filter logic uses `if ceiling and amt_min is not None and amt_min > ceiling: continue`.
- `main.py` tool schema: "Only return grants available at or below this amount
  (a ceiling, in the grant's own currency)."
- No stale "floors on legacy" comment remains.

**U1 was NOT re-done this batch — it was already complete. STEP 2 skipped.**

## Per-unit summary

| Unit | Description | Commit | Status |
|------|-------------|--------|--------|
| U1 | `search_grant_programs` max_award = true CEILING + schema wording | `d2e0909` | Pre-existing (prior session); verified present |
| U2 | `search_curators` — drop unapplied platform/min_followers params (M5) | `5dd4ff6` | This batch |
| U3 | Wire Jade `suggest_crowdfunding` — schema entry + dispatch branch | `c47d3d7` | This batch |
| U4 | M1: await Buffer OAuth token exchange (non-blocking async client) | `791f0df` | This batch |
| U5 | M2: batch Gmail message fetch in `detect_replies` (kill N+1) | `f6afffa` | This batch |
| U6 | M4: remove dead `music_edu_service.py` (zero import sites) | `f785c79` | This batch |

## U5 detail (M2 — N+1 Gmail fetch)

- `pitch_service.py::detect_replies` — replaced the per-message
  `service.users().messages().get(...).execute()` loop (up to 50 sequential
  round-trips) with a single `service.new_batch_http_request()` /
  `BatchHttpRequest`. Per-message fetch errors are skipped (message can't be
  matched/classified); `GmailNotConnected` / `GmailAuthExpired` degradation
  (raised earlier in `_get_gmail_service`) and the `{scanned, matched,
  classified}` output shape are unchanged.
- New `tests/test_pitch_reply_scan_batch.py` — fully scripted fake Gmail service
  (zero real API calls) proving: exactly one `batch.execute()` and zero
  individual `get().execute()` (N+1 gone); output shape preserved across
  multiple messages; an errored message is skipped while healthy ones still
  process.
- `tests/test_pitch_service.py` + `tests/integration/conftest.py` — the shared
  `mock_gmail_service` helper and the local `_make_gmail_svc` helper were taught
  to script `new_batch_http_request` for the batch path **while keeping**
  `get().execute()` scripting for `pr_service` / `booking_service` consumers,
  which still fetch per-message. **conftest change verdict: U5-related and
  necessary** — `mock_gmail_service` is a shared integration fixture consumed by
  `test_pitch_lifecycle.py` and `test_full_artist_journey.py` (which drive
  `detect_replies`) plus `test_pr_lifecycle.py` / `test_booking_lifecycle.py` /
  `test_artist_onboarding_flow.py` (per-message consumers). Minimal, no
  unrelated changes.

## U6 detail (M4 — dead module removal)

- `git rm music_edu_service.py`. Verified ZERO import sites: no
  `import music_edu_service` / `from music_edu_service`, no string/tool-name
  reference in `main.py`, and every reference to its public symbols
  (`search_courses`, `build_learning_plan`, `enroll_in_course`, `_get_course`,
  `_learning_account_connected`) was internal to the file itself.
- The only external `music_edu` mention is `tests/test_p3e_music-edu.py`, which
  tests the music-edu **agent's** cross-domain routing via
  `knowledge_bank.agent_home` — unrelated to this module. No dead references
  elsewhere to clean up.
- Collect count unchanged (module held no tests).

## Verification

- Entity gate (`assert_no_forbidden_terms`) run on each staged diff → clean.
- Entity guards by name (`-k "forbidden or entity_wall"`) → 79 passed, 0 failed.
- Full suite reconciled vs `--collect-only`: 2902 collected.
- Full suite on branch (post-U5): 2902 passed / 0 failed / 0 errors.
- Full suite on branch (post-U6): 2902 passed / 0 failed / 0 errors.
- Full suite on main (post-merge): **2902 passed / 0 failed / 0 errors** (27 chunks).

## Merge

- Prior main tip: `e7b6850` (verified == origin/main before merge — unmoved).
- Merge type: **fast-forward-only** (`--ff-only`); no force, no rewrite.
- New main tip: `f785c79`.
