"""
R-28 — Weekly report scheduler configurable via env vars.

Tests:
- Default schedule is Sunday 18:00 UTC when env vars are absent
- WEEKLY_REPORT_DAY overrides the day_of_week on the registered job
- WEEKLY_REPORT_HOUR_UTC overrides the hour
- WEEKLY_REPORT_MINUTE overrides the minute
"""

import importlib
from unittest.mock import MagicMock, patch

import pytest


def _make_scheduler():
    """Return a MagicMock APScheduler that records add_job calls."""
    sched = MagicMock()
    sched.running = True
    return sched


def _reload_social(monkeypatch, **env_overrides):
    """Reload social_service with the given env vars set (and scheduler enabled)."""
    monkeypatch.setenv("SCHEDULER_ENABLED", "true")
    for key, val in env_overrides.items():
        monkeypatch.setenv(key, str(val))

    import social_service
    importlib.reload(social_service)
    return social_service


def _get_job_kwargs(mock_scheduler):
    """Extract the keyword arguments from the first add_job call."""
    assert mock_scheduler.add_job.called, "add_job was never called"
    _, kwargs = mock_scheduler.add_job.call_args
    return kwargs


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_default_schedule_is_sunday_18_utc(monkeypatch):
    """When no schedule env vars are set, the job runs Sunday at 18:00 UTC."""
    monkeypatch.delenv("WEEKLY_REPORT_DAY",      raising=False)
    monkeypatch.delenv("WEEKLY_REPORT_HOUR_UTC", raising=False)
    monkeypatch.delenv("WEEKLY_REPORT_MINUTE",   raising=False)

    social = _reload_social(monkeypatch)
    mock_sched = _make_scheduler()

    with patch("pitch_service._scheduler", mock_sched):
        social.init_report_scheduler()

    kw = _get_job_kwargs(mock_sched)
    assert kw.get("day_of_week") == "sun"
    assert kw.get("hour")        == 18
    assert kw.get("minute")      == 0


def test_weekly_report_day_override(monkeypatch):
    """WEEKLY_REPORT_DAY changes the day_of_week on the registered cron job."""
    social = _reload_social(monkeypatch, WEEKLY_REPORT_DAY="wed")
    mock_sched = _make_scheduler()

    with patch("pitch_service._scheduler", mock_sched):
        social.init_report_scheduler()

    kw = _get_job_kwargs(mock_sched)
    assert kw.get("day_of_week") == "wed"
    # Other fields still at defaults
    assert kw.get("hour")   == 18
    assert kw.get("minute") == 0


def test_weekly_report_hour_override(monkeypatch):
    """WEEKLY_REPORT_HOUR_UTC changes the hour on the registered cron job."""
    social = _reload_social(monkeypatch, WEEKLY_REPORT_HOUR_UTC="9")
    mock_sched = _make_scheduler()

    with patch("pitch_service._scheduler", mock_sched):
        social.init_report_scheduler()

    kw = _get_job_kwargs(mock_sched)
    assert kw.get("hour")        == 9
    assert kw.get("day_of_week") == "sun"
    assert kw.get("minute")      == 0


def test_weekly_report_minute_override(monkeypatch):
    """WEEKLY_REPORT_MINUTE changes the minute on the registered cron job."""
    social = _reload_social(monkeypatch, WEEKLY_REPORT_MINUTE="30")
    mock_sched = _make_scheduler()

    with patch("pitch_service._scheduler", mock_sched):
        social.init_report_scheduler()

    kw = _get_job_kwargs(mock_sched)
    assert kw.get("minute")      == 30
    assert kw.get("day_of_week") == "sun"
    assert kw.get("hour")        == 18


def test_all_schedule_overrides_combined(monkeypatch):
    """All three env vars can be overridden simultaneously."""
    social = _reload_social(
        monkeypatch,
        WEEKLY_REPORT_DAY="fri",
        WEEKLY_REPORT_HOUR_UTC="6",
        WEEKLY_REPORT_MINUTE="15",
    )
    mock_sched = _make_scheduler()

    with patch("pitch_service._scheduler", mock_sched):
        social.init_report_scheduler()

    kw = _get_job_kwargs(mock_sched)
    assert kw.get("day_of_week") == "fri"
    assert kw.get("hour")        == 6
    assert kw.get("minute")      == 15
