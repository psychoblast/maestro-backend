"""
A4 — Request-level performance metrics.

Tests:
- Server-Timing header present on every response
- Slow request (>2s) triggers WARNING log
- Performance endpoint returns correct p50/p95/p99 after sample traffic
"""

import importlib
import time
from unittest.mock import MagicMock, patch

import pytest


# ── helpers ────────────────────────────────────────────────────────────────────

_PLMKR_KEY = "timing-test-key"


def _build_client(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH",           str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",      "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",   str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",       str(tmp_path / "artists"))
    monkeypatch.setenv("PLMKR_API_KEY",     _PLMKR_KEY)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)

    import performance_metrics as pm
    importlib.reload(pm)

    from fastapi.testclient import TestClient
    return TestClient(m.app, raise_server_exceptions=False), m, pm


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_server_timing_header_present(monkeypatch, tmp_path):
    """Every response must include a Server-Timing header with duration."""
    client, m, pm = _build_client(monkeypatch, tmp_path)
    resp = client.get("/health")
    assert "server-timing" in resp.headers
    assert "total;dur=" in resp.headers["server-timing"]


def test_server_timing_value_is_numeric(monkeypatch, tmp_path):
    """Server-Timing dur value must be a non-negative float."""
    client, m, pm = _build_client(monkeypatch, tmp_path)
    resp = client.get("/health")
    header = resp.headers["server-timing"]  # e.g. "total;dur=3.2"
    dur_str = header.split("dur=")[1]
    dur = float(dur_str)
    assert dur >= 0.0


def test_slow_request_triggers_warning(monkeypatch, tmp_path):
    """Requests exceeding the slow-request threshold must call logger.warning."""
    client, m, pm = _build_client(monkeypatch, tmp_path)

    # Lower the threshold to 0 so every request qualifies as "slow"
    monkeypatch.setattr(m, "_SLOW_REQUEST_THRESHOLD_MS", 0.0)

    warning_calls: list = []

    def _capture_warning(msg, *args, **kwargs):
        warning_calls.append(msg)

    timing_logger = __import__("logging").getLogger("timing")
    with patch.object(timing_logger, "warning", side_effect=_capture_warning):
        client.get("/health")

    assert warning_calls, "Expected logger('timing').warning to be called for slow request"
    assert "slow_request" in str(warning_calls[0])


def test_performance_endpoint_returns_percentiles(monkeypatch, tmp_path):
    """After sample traffic, /api/admin/diagnostics/performance must return p50/p95/p99."""
    client, m, pm = _build_client(monkeypatch, tmp_path)

    # Generate enough traffic to fill the rolling window sample
    for _ in range(10):
        client.get("/health")

    resp = client.get(
        "/api/admin/diagnostics/performance",
        headers={"X-API-Key": _PLMKR_KEY},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "routes" in body
    assert "timestamp" in body
    routes = body["routes"]
    # /health should be recorded
    assert "/health" in routes, f"Expected /health in routes. Got: {list(routes.keys())}"
    health_stats = routes["/health"]
    for key in ("p50", "p95", "p99", "count"):
        assert key in health_stats, f"Missing key {key} in {health_stats}"
    assert health_stats["count"] >= 10


def test_performance_endpoint_401_without_key(monkeypatch, tmp_path):
    """Performance endpoint must require API key."""
    client, m, pm = _build_client(monkeypatch, tmp_path)
    resp = client.get("/api/admin/diagnostics/performance")
    assert resp.status_code == 401
