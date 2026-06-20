"""
Tests for GET /api/agents/ar-scout/assess/demo — HTML scorecard renderer.

All tests are in-process. No live network calls.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from entity_wall_terms import assert_no_forbidden_terms


def _load_app(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-ant-test")
    monkeypatch.setenv("AR_SCOUT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


def test_demo_returns_200(monkeypatch, tmp_path):
    """Demo endpoint returns 200."""
    client = _load_app(monkeypatch, tmp_path)
    resp = client.get("/api/agents/ar-scout/assess/demo")
    assert resp.status_code == 200


def test_demo_content_type_html(monkeypatch, tmp_path):
    """Demo endpoint returns HTML content-type."""
    client = _load_app(monkeypatch, tmp_path)
    resp = client.get("/api/agents/ar-scout/assess/demo")
    assert "text/html" in resp.headers.get("content-type", "")


def test_demo_contains_verdict(monkeypatch, tmp_path):
    """Rendered HTML contains a verdict from the rubric."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text

    valid_verdicts = ["PASS", "WATCH", "DEVELOP", "PURSUE", "GREENLIGHT", "SIGN IMMEDIATELY"]
    assert any(v in html for v in valid_verdicts), "No valid verdict found in demo HTML"


def test_demo_contains_all_five_pillar_labels(monkeypatch, tmp_path):
    """HTML scorecard renders labels for all five pillars."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text

    pillar_labels = [
        "Music Quality",
        "Artist Identity",
        "Audience",
        "Execution",
        "Commercial Opportunity",
    ]
    for label in pillar_labels:
        assert label in html, f"Pillar label '{label}' not found in HTML"


def test_demo_contains_hard_gates(monkeypatch, tmp_path):
    """HTML scorecard includes hard gate status section."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text

    assert "Gate 1" in html
    assert "Gate 2" in html
    assert "Gate 3" in html
    assert "Gate 4" in html


def test_demo_contains_provisional_label(monkeypatch, tmp_path):
    """HTML scorecard shows PROVISIONAL composite label."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text
    assert "PROVISIONAL" in html


def test_demo_contains_risk_assessment(monkeypatch, tmp_path):
    """HTML scorecard renders risk assessment section."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text
    assert "Risk Assessment" in html or "risk" in html.lower()


def test_demo_contains_five_year_test(monkeypatch, tmp_path):
    """HTML scorecard renders Five-Year Test section."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text
    assert "Five-Year Test" in html or "five years" in html.lower()


def test_demo_contains_sample_artist_name(monkeypatch, tmp_path):
    """Demo page renders a sample artist name."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text
    assert "Jordan Voss" in html  # the sample artist embedded in the demo


def test_demo_no_entity_strings_in_html(monkeypatch, tmp_path):
    """Rendered HTML must not contain forbidden entity strings."""
    client = _load_app(monkeypatch, tmp_path)
    html = client.get("/api/agents/ar-scout/assess/demo").text

    assert_no_forbidden_terms(html)


def test_mocked_e2e_assess_then_render(monkeypatch, tmp_path):
    """
    Full mocked end-to-end: POST assess → check scorecard fields are
    renderable → GET demo renders without error.
    """
    client = _load_app(monkeypatch, tmp_path)

    # Step 1: POST assessment
    payload = {
        "artist": {"name": "E2E Artist", "genre": "Hip-Hop", "stage": "developing",
                   "territory": "US", "monthly_listeners": 150000, "save_rate": 0.05,
                   "release_count": 8, "manager": "Test Manager", "label": None},
        "track":  {"title": "E2E Track", "bpm": 140.0, "duration_sec": 185.0,
                   "lufs": -13.8, "intro_length_sec": 8.0,
                   "genre": None, "features": ["Featured Artist"], "release_date": None},
        "evaluation_stage": "approach",
        "additional_notes": "Strong social presence.",
    }
    resp = client.post("/api/agents/ar-scout/assess", json=payload)
    assert resp.status_code == 200
    body = resp.json()

    # Verify all scorecard fields present in JSON response
    assert "pillars" in body["assessment"]
    assert "verdict" in body["assessment"]
    assert "composite" in body["assessment"]
    assert body["assessment"]["composite"]["label"] == "PROVISIONAL"

    # Step 2: GET demo still renders
    demo_resp = client.get("/api/agents/ar-scout/assess/demo")
    assert demo_resp.status_code == 200
    assert "PLMKR A&R Assessment" in demo_resp.text
