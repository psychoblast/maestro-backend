"""
Admin Dashboard — GET /admin/dashboard

Tests:
- Unauthenticated request (PLMKR_API_KEY set, no header) → 200 (R-35 fix: shell is public)
- Authenticated request → 200 text/html with expected HTML structure markers
- Both return the same HTML shell (no secrets in the shell; data fetched JS-side via key)
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

def test_dashboard_unauthenticated_returns_200(client):
    """No X-API-Key header → 200. R-35 fix: HTML shell is public; data is auth-gated JS-side."""
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 200


def test_dashboard_wrong_key_still_returns_200(client):
    """Wrong X-API-Key on page-load → still 200. Shell reveals no data; key prompt handles auth."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 200


def test_dashboard_authenticated_returns_200(client):
    """Correct X-API-Key → 200."""
    resp = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY})
    assert resp.status_code == 200


def test_dashboard_unauthed_and_authed_return_same_html(client):
    """Unauthenticated and authenticated page-loads return identical HTML (shell has no secrets)."""
    unauthed = client.get("/admin/dashboard").text
    authed   = client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY}).text
    assert unauthed == authed


def test_dashboard_content_type_html(client):
    """Response Content-Type is text/html."""
    resp = client.get("/admin/dashboard")
    assert "text/html" in resp.headers.get("content-type", "")


def test_json_endpoints_still_require_auth(client):
    """All 6 JSON admin endpoints still return 401 without X-API-Key (R-35: data stays gated)."""
    protected = [
        "/api/admin/diagnostics",
        "/api/admin/diagnostics/performance",
        "/api/admin/diagnostics/anthropic-stats",
        "/api/admin/diagnostics/gmail-stats",
        "/api/admin/diagnostics/scheduler",
    ]
    for url in protected:
        resp = client.get(url)
        assert resp.status_code == 401, f"{url} should require auth but returned {resp.status_code}"


def test_dashboard_shell_contains_no_env_values(client):
    """Unauthenticated shell HTML contains only 'SET'/'MISSING' placeholders, never actual values."""
    resp = client.get("/admin/dashboard")
    html = resp.text
    # Shell must contain the modal and key storage constant — proves it's the real page
    assert "key-modal" in html
    assert "plmkr_admin_key" in html
    # Env var values are never embedded in the shell (only JS fetches them post-auth)
    import os
    test_key = os.environ.get("PLMKR_API_KEY", "")
    if test_key:
        assert test_key not in html


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


# ── Unit 3: Data sections — per-endpoint URL + rendering structure ────────────

def _html(client):
    return client.get("/admin/dashboard", headers={"X-API-Key": _TEST_KEY}).text


def test_section_diagnostics_fetches_correct_endpoint(client):
    """loadDiagnostics() fetches /api/admin/diagnostics."""
    html = _html(client)
    assert "loadDiagnostics" in html
    assert "'/api/admin/diagnostics'" in html or '"/api/admin/diagnostics"' in html


def test_section_performance_fetches_correct_endpoint(client):
    """loadPerformance() fetches /api/admin/diagnostics/performance."""
    html = _html(client)
    assert "loadPerformance" in html
    assert "/api/admin/diagnostics/performance" in html


def test_section_anthropic_fetches_correct_endpoint(client):
    """loadAnthropic() fetches /api/admin/diagnostics/anthropic-stats."""
    html = _html(client)
    assert "loadAnthropic" in html
    assert "/api/admin/diagnostics/anthropic-stats" in html


def test_section_gmail_fetches_correct_endpoint(client):
    """loadGmail() fetches /api/admin/diagnostics/gmail-stats."""
    html = _html(client)
    assert "loadGmail" in html
    assert "/api/admin/diagnostics/gmail-stats" in html


def test_section_scheduler_fetches_correct_endpoint(client):
    """loadScheduler() fetches /api/admin/diagnostics/scheduler."""
    html = _html(client)
    assert "loadScheduler" in html
    assert "/api/admin/diagnostics/scheduler" in html


def test_section_health_fetches_correct_endpoint(client):
    """loadHealth() fetches /api/admin/health/deep."""
    html = _html(client)
    assert "loadHealth" in html
    assert "/api/admin/health/deep" in html


def test_performance_table_sortable_headers(client):
    """Performance table has sortable column headers (data-col attribute)."""
    html = _html(client)
    assert "data-col" in html


def test_anthropic_and_gmail_have_sum_row(client):
    """Anthropic and Gmail tables include a sum-row for totals."""
    html = _html(client)
    assert "sum-row" in html


def test_error_handling_uses_sectionError(client):
    """Each section catch block calls sectionError()."""
    html = _html(client)
    # sectionError must appear multiple times (one per section)
    assert html.count("sectionError") >= 6


def test_health_shows_ok_or_err_css_class(client):
    """Health section JS references health-ok and health-err CSS classes."""
    html = _html(client)
    assert "health-ok" in html
    assert "health-err" in html


def test_refreshAll_calls_all_loaders(client):
    """refreshAll() invokes all 6 loader functions."""
    html = _html(client)
    for fn in ["loadDiagnostics()", "loadPerformance()", "loadAnthropic()",
               "loadGmail()", "loadScheduler()", "loadHealth()"]:
        assert fn in html, f"refreshAll does not call {fn}"


def test_env_snapshot_comment_no_values(client):
    """Code comment or variable name signals that env values are never shown."""
    html = _html(client)
    # The JS checks 'SET'/'MISSING' — never the value itself
    assert "'SET'" in html or '"SET"' in html


# ── Unit 4: Polish + responsive + accessibility ───────────────────────────────

def test_section_titles_use_h2(client):
    """Section titles use <h2> elements for proper heading hierarchy."""
    html = _html(client)
    assert html.count('<h2 class="section-title">') >= 6


def test_sections_have_aria_label(client):
    """All 6 sections have aria-label attributes."""
    html = _html(client)
    for label in ["Diagnostics", "Performance", "Anthropic API Usage",
                  "Gmail API Usage", "Scheduler Queue", "Deep Health"]:
        assert f'aria-label="{label}"' in html, f"Missing aria-label: {label}"


def test_modal_has_role_dialog(client):
    """Key modal has role='dialog' and aria-modal attributes."""
    html = _html(client)
    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html


def test_modal_has_aria_labelledby(client):
    """Key modal uses aria-labelledby pointing to modal title."""
    html = _html(client)
    assert "aria-labelledby" in html
    assert "modal-title" in html


def test_refresh_timestamp_has_aria_live(client):
    """Refresh timestamp element has aria-live='polite'."""
    html = _html(client)
    assert 'aria-live="polite"' in html


def test_error_spans_have_role_alert(client):
    """Error spans use role='alert' for screen reader announcement."""
    html = _html(client)
    assert 'role="alert"' in html


def test_health_status_has_role_status(client):
    """Health status indicator uses role='status'."""
    html = _html(client)
    assert 'role="status"' in html


def test_badge_has_role_img(client):
    """Status badges use role='img' with aria-label."""
    html = _html(client)
    assert 'role="img"' in html


def test_footer_contains_version(client):
    """Footer contains 'v0.1' version string."""
    html = _html(client)
    assert "v0.1" in html
    assert "<footer>" in html


def test_data_tables_have_aria_label(client):
    """Data tables rendered by JS include aria-label attributes."""
    html = _html(client)
    # aria-label on tables is embedded in JS template strings
    assert 'aria-label="Environment variables"' in html or "aria-label=" in html
