"""
R-27 — SCHEDULER_ENABLED three-state flag.

Tests:
- SCHEDULER_ENABLED unset → init_scheduler() is a no-op; emits scheduler_disabled
- SCHEDULER_ENABLED=dry_run → _poll_all() logs would_have_fired, does NOT call detect_replies
- SCHEDULER_ENABLED=dry_run → _generate_all_weekly_reports() logs would_have_fired, does NOT call DB/Anthropic
- SCHEDULER_ENABLED=dry_run → execute_all_due_campaign_actions() logs would_have_fired, does NOT call _db_list_due_actions
- SCHEDULER_ENABLED=true → _poll_all() calls _get_artists_with_sent_pitches (real code path)
- SCHEDULER_ENABLED=true → execute_all_due_campaign_actions() calls _db_list_due_actions (real code path)
"""

import asyncio
import importlib


# ── helpers ───────────────────────────────────────────────────────────────────

def _capture_info(module):
    """Monkey-patch module.log.info to capture extra dicts; return the list."""
    calls = []
    module.log.info = lambda msg, *a, **kw: calls.append(kw.get("extra", {}))
    return calls


def _event_names(calls):
    return [c.get("event", "") for c in calls]


# ── Test 1: unset → init_scheduler is a no-op ────────────────────────────────

def test_scheduler_disabled_when_env_unset(monkeypatch):
    """SCHEDULER_ENABLED unset → init_scheduler() logs scheduler_disabled and _scheduler stays None."""
    monkeypatch.delenv("SCHEDULER_ENABLED", raising=False)
    import pitch_service
    importlib.reload(pitch_service)

    info_calls = _capture_info(pitch_service)
    original_info = pitch_service.log.info
    try:
        pitch_service.init_scheduler()
    finally:
        pitch_service.log.info = original_info

    assert "scheduler_disabled" in _event_names(info_calls), (
        f"Expected scheduler_disabled event. Got: {_event_names(info_calls)}"
    )
    assert pitch_service._scheduler is None


# ── Test 2: dry_run → _poll_all logs would_have_fired, skip detect_replies ───

def test_poll_all_dry_run_logs_would_have_fired(monkeypatch):
    """SCHEDULER_ENABLED=dry_run → _poll_all() emits would_have_fired/inbox_poll; detect_replies NOT called."""
    monkeypatch.setenv("SCHEDULER_ENABLED", "dry_run")
    import pitch_service
    importlib.reload(pitch_service)

    info_calls = _capture_info(pitch_service)
    original_info = pitch_service.log.info

    detect_called = []
    original_detect = pitch_service.detect_replies
    pitch_service.detect_replies = lambda *a, **kw: detect_called.append(True)

    try:
        asyncio.run(pitch_service._poll_all())
    finally:
        pitch_service.log.info = original_info
        pitch_service.detect_replies = original_detect

    would_have = [c for c in info_calls if c.get("event") == "would_have_fired"]
    assert would_have, f"No would_have_fired events logged. Got: {info_calls}"
    assert any(c.get("job_id") == "inbox_poll" for c in would_have), (
        f"Expected job_id=inbox_poll. Got: {would_have}"
    )
    assert not detect_called, "detect_replies must NOT be called in dry_run mode"


# ── Test 3: dry_run → _generate_all_weekly_reports logs would_have_fired ─────

def test_weekly_reports_dry_run_logs_would_have_fired(monkeypatch):
    """SCHEDULER_ENABLED=dry_run → _generate_all_weekly_reports() emits would_have_fired/weekly_reports."""
    monkeypatch.setenv("SCHEDULER_ENABLED", "dry_run")
    import social_service
    importlib.reload(social_service)

    info_calls = _capture_info(social_service)
    original_info = social_service.log.info

    # Ensure the real DB/Anthropic path is not called by patching _get_artists_with_any_activity
    get_artists_called = []
    original_get = social_service._get_artists_with_any_activity
    social_service._get_artists_with_any_activity = lambda: get_artists_called.append(True) or []

    try:
        asyncio.run(social_service._generate_all_weekly_reports())
    finally:
        social_service.log.info = original_info
        social_service._get_artists_with_any_activity = original_get

    would_have = [c for c in info_calls if c.get("event") == "would_have_fired"]
    assert would_have, f"No would_have_fired events logged. Got: {info_calls}"
    assert any(c.get("job_id") == "weekly_reports" for c in would_have), (
        f"Expected job_id=weekly_reports. Got: {would_have}"
    )
    assert not get_artists_called, "_get_artists_with_any_activity must NOT be called in dry_run mode"


# ── Test 4: dry_run → execute_all_due_campaign_actions logs would_have_fired ─

def test_campaign_executor_dry_run_logs_would_have_fired(monkeypatch):
    """SCHEDULER_ENABLED=dry_run → execute_all_due_campaign_actions() emits would_have_fired/campaign_executor."""
    monkeypatch.setenv("SCHEDULER_ENABLED", "dry_run")
    import release_service
    importlib.reload(release_service)

    info_calls = _capture_info(release_service)
    original_info = release_service.log.info

    db_list_called = []
    original_db_list = release_service._db_list_due_actions
    release_service._db_list_due_actions = lambda: db_list_called.append(True) or []

    try:
        asyncio.run(release_service.execute_all_due_campaign_actions())
    finally:
        release_service.log.info = original_info
        release_service._db_list_due_actions = original_db_list

    would_have = [c for c in info_calls if c.get("event") == "would_have_fired"]
    assert would_have, f"No would_have_fired events logged. Got: {info_calls}"
    assert any(c.get("job_id") == "campaign_executor" for c in would_have), (
        f"Expected job_id=campaign_executor. Got: {would_have}"
    )
    assert not db_list_called, "_db_list_due_actions must NOT be called in dry_run mode"


# ── Test 5: true → _poll_all actually enters real code path ──────────────────

def test_poll_all_live_calls_get_artists(monkeypatch):
    """SCHEDULER_ENABLED=true → _poll_all() calls _get_artists_with_sent_pitches (live path)."""
    monkeypatch.setenv("SCHEDULER_ENABLED", "true")
    import pitch_service
    importlib.reload(pitch_service)

    get_artists_called = []
    original_get = pitch_service._get_artists_with_sent_pitches
    pitch_service._get_artists_with_sent_pitches = lambda: get_artists_called.append(True) or []

    try:
        asyncio.run(pitch_service._poll_all())
    finally:
        pitch_service._get_artists_with_sent_pitches = original_get

    assert get_artists_called, "_get_artists_with_sent_pitches must be called in live mode"


# ── Test 6: true → execute_all_due_campaign_actions enters real code path ────

def test_campaign_executor_live_calls_db_list_due_actions(monkeypatch):
    """SCHEDULER_ENABLED=true → execute_all_due_campaign_actions() calls _db_list_due_actions (live path)."""
    monkeypatch.setenv("SCHEDULER_ENABLED", "true")
    import release_service
    importlib.reload(release_service)

    db_list_called = []
    original_db_list = release_service._db_list_due_actions
    release_service._db_list_due_actions = lambda: db_list_called.append(True) or []

    try:
        asyncio.run(release_service.execute_all_due_campaign_actions())
    finally:
        release_service._db_list_due_actions = original_db_list

    assert db_list_called, "_db_list_due_actions must be called in live mode"
