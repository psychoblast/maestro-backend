"""
Admin Dashboard — GET /admin/dashboard

Tests:
- Unauthenticated request (PLMKR_API_KEY set, no header) → 401
- Authenticated request → 200 text/html with expected HTML structure markers
- Expected section IDs present in HTML (all 6 sections)
- Route appears in OpenAPI schema
"""

import importlib
from unittest.mock import MagicMock, patch

import pytest

_TEST_KEY = "dashboard-test-key"


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_PATH",           str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",      "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",   str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",       str(tmp_path / "artists"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("PLMKR_API_KEY",     _TEST_KEY)

    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)

    from fastapi.testclient import TestClient
    return TestClient(m.app, raise_server_exceptions=False)


# ── Auth tests ────────────────────────────────────────────────────────────────

def test_dashboard_unauthenticated_returns_401(client):
    """No X-API-Key header → 401 (same middleware as all protected routes)."""
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 401


def test_dashboard_wrong_key_returns_401(client):
    """Wrong X-API-Key → 401."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_dashboard_authenticated_returns_200(client):
    """Correct X-API-Key → 200."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert resp.status_code == 200


def test_dashboard_content_type_html(client):
    """Response Content-Type is text/html."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "text/html" in resp.headers.get("content-type", "")


# ── HTML structure tests ──────────────────────────────────────────────────────

def test_dashboard_has_title(client):
    """Page <title> contains 'PLMKR Admin Dashboard'."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "PLMKR Admin Dashboard" in resp.text


def test_dashboard_has_all_6_sections(client):
    """All 6 section containers are present in the HTML."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    html = resp.text
    for section_id in ["s-diagnostics", "s-performance", "s-anthropic",
                       "s-gmail", "s-scheduler", "s-health"]:
        assert section_id in html, f"Missing section: {section_id}"


def test_dashboard_has_key_modal(client):
    """Page contains the key prompt modal."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "key-modal" in resp.text


def test_dashboard_has_pause_and_signout_controls(client):
    """Page contains pause and sign-out buttons."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "pause-btn" in resp.text
    assert "signout-btn" in resp.text


def test_dashboard_references_all_6_api_endpoints(client):
    """JS template references all 6 expected admin endpoint URLs."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    html = resp.text
    for endpoint in [
        "/api/admin/diagnostics",
        "/api/admin/diagnostics/performance",
        "/api/admin/diagnostics/anthropic-stats",
        "/api/admin/diagnostics/gmail-stats",
        "/api/admin/diagnostics/scheduler",
        "/api/admin/health/deep",
    ]:
        assert endpoint in html, f"Missing endpoint reference in template: {endpoint}"


# ── OpenAPI schema test ───────────────────────────────────────────────────────

def test_dashboard_in_openapi_schema(client):
    """GET /admin/dashboard appears in the OpenAPI schema."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json().get("paths", {})
    assert "/admin/dashboard" in paths, f"/admin/dashboard not in OpenAPI paths: {list(paths)[:20]}"


# ── Unit 2: JS key flow + visual shell assertions ─────────────────────────────

def test_dashboard_uses_correct_session_storage_key(client):
    """JS uses 'plmkr_admin_key' as the sessionStorage key name."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "plmkr_admin_key" in resp.text


def test_dashboard_section_loading_placeholders(client):
    """All 6 section data containers start with 'Loading' placeholder text."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    html = resp.text
    for data_id in ["d-diagnostics", "d-performance", "d-anthropic",
                    "d-gmail", "d-scheduler", "d-health"]:
        assert data_id in html, f"Missing data container: {data_id}"
    assert "Loading" in html


def test_dashboard_pause_button_initial_aria(client):
    """Pause button starts with aria-pressed='false'."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert 'aria-pressed="false"' in resp.text


def test_dashboard_auto_refresh_interval_defined(client):
    """30-second auto-refresh constant (30_000 ms) is present in JS."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "30_000" in resp.text or "30000" in resp.text


def test_dashboard_signout_uses_window_confirm(client):
    """Sign-out uses window.confirm for confirmation."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "window.confirm" in resp.text


def test_dashboard_401_clears_key_and_reprompts(client):
    """apiFetch handler clears sessionStorage and calls showModal on 401/403."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    html = resp.text
    # Both clearKey() and showModal() must appear in the 401 handler code path
    assert "clearKey()" in html
    assert "showModal()" in html


def test_dashboard_mobile_viewport_meta(client):
    """Page includes viewport meta tag for mobile rendering."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert 'name="viewport"' in resp.text
    assert "width=device-width" in resp.text


def test_dashboard_responsive_media_query(client):
    """CSS includes a max-width media query for responsive layout."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert "@media" in resp.text and "max-width" in resp.text
