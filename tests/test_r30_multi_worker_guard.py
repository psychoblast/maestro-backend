"""
R-30 — Multi-worker scheduler guard.

Tests:
- WEB_CONCURRENCY=2 → init_scheduler() logs CRITICAL and returns before importing apscheduler
- WEB_CONCURRENCY=1 → WEB_CONCURRENCY guard does NOT fire (apscheduler absent → ImportError path)
- WEB_CONCURRENCY unset → defaults to 1; guard does NOT fire
- SCHEDULER_ENABLED=false → guard not reached; no log from guard
"""

import importlib
from unittest.mock import MagicMock, call, patch

import pytest


def _reload_pitch(monkeypatch, *, scheduler_enabled: bool = True, web_concurrency: str = None):
    monkeypatch.setenv("SCHEDULER_ENABLED", "true" if scheduler_enabled else "false")
    if web_concurrency is not None:
        monkeypatch.setenv("WEB_CONCURRENCY", web_concurrency)
    else:
        monkeypatch.delenv("WEB_CONCURRENCY", raising=False)

    import pitch_service
    importlib.reload(pitch_service)
    return pitch_service


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_multi_worker_guard_logs_critical_and_skips(monkeypatch):
    """WEB_CONCURRENCY=2 → log.critical emitted; _scheduler stays None."""
    pitch = _reload_pitch(monkeypatch, scheduler_enabled=True, web_concurrency="2")

    critical_calls = []
    original_critical = pitch.log.critical
    pitch.log.critical = lambda msg, *a, **kw: critical_calls.append((msg, kw.get("extra", {})))

    try:
        pitch.init_scheduler()
    finally:
        pitch.log.critical = original_critical

    assert pitch._scheduler is None
    assert any(
        "WEB_CONCURRENCY" in str(extra) or "duplicate" in str(extra)
        for _, extra in critical_calls
    ), f"Expected multi-worker CRITICAL log. Got: {critical_calls}"


def test_multi_worker_guard_does_not_fire_for_single_worker(monkeypatch):
    """WEB_CONCURRENCY=1 → guard CRITICAL is NOT emitted (ImportError path is fine)."""
    pitch = _reload_pitch(monkeypatch, scheduler_enabled=True, web_concurrency="1")

    critical_calls = []
    original_critical = pitch.log.critical
    pitch.log.critical = lambda msg, *a, **kw: critical_calls.append((msg, kw.get("extra", {})))

    try:
        pitch.init_scheduler()
    finally:
        pitch.log.critical = original_critical

    # Guard must not have fired
    concurrency_criticals = [
        (msg, extra) for msg, extra in critical_calls
        if "WEB_CONCURRENCY" in str(extra)
    ]
    assert not concurrency_criticals, (
        f"Multi-worker guard should not fire for WEB_CONCURRENCY=1. Got: {concurrency_criticals}"
    )
    # _scheduler is None because apscheduler isn't installed — that's fine for this test
    assert pitch._scheduler is None


def test_unset_web_concurrency_guard_does_not_fire(monkeypatch):
    """WEB_CONCURRENCY unset → defaults to 1; CRITICAL guard not emitted."""
    pitch = _reload_pitch(monkeypatch, scheduler_enabled=True, web_concurrency=None)

    critical_calls = []
    original_critical = pitch.log.critical
    pitch.log.critical = lambda msg, *a, **kw: critical_calls.append((msg, kw.get("extra", {})))

    try:
        pitch.init_scheduler()
    finally:
        pitch.log.critical = original_critical

    concurrency_criticals = [
        (msg, extra) for msg, extra in critical_calls
        if "WEB_CONCURRENCY" in str(extra)
    ]
    assert not concurrency_criticals


def test_scheduler_disabled_guard_never_reached(monkeypatch):
    """SCHEDULER_ENABLED=false → guard is not reached; no CRITICAL log from guard."""
    pitch = _reload_pitch(monkeypatch, scheduler_enabled=False, web_concurrency="3")

    critical_calls = []
    original_critical = pitch.log.critical
    pitch.log.critical = lambda msg, *a, **kw: critical_calls.append((msg, kw.get("extra", {})))

    try:
        pitch.init_scheduler()
    finally:
        pitch.log.critical = original_critical

    # The SCHEDULER_ENABLED guard fires first; WEB_CONCURRENCY guard never reached
    concurrency_criticals = [
        (msg, extra) for msg, extra in critical_calls
        if "WEB_CONCURRENCY" in str(extra)
    ]
    assert not concurrency_criticals
    assert pitch._scheduler is None
