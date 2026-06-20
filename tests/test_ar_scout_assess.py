"""
Tests for POST /api/agents/ar-scout/assess route.

All tests use mocks only. No live Anthropic calls.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from entity_wall_terms import assert_no_forbidden_terms


# ── test fixtures ──────────────────────────────────────────────────────────────

SAMPLE_PAYLOAD = {
    "artist": {
        "name":             "Test Artist",
        "genre":            "R&B",
        "stage":            "emerging",
        "territory":        "Canada",
        "monthly_listeners": 25000,
        "save_rate":        0.06,
        "release_count":    3,
        "manager":          None,
        "label":            None,
    },
    "track": {
        "title":            "Sample Track",
        "bpm":              96.0,
        "duration_sec":     198.0,
        "lufs":             -14.2,
        "intro_length_sec": 12.0,
        "genre":            None,
        "features":         [],
        "release_date":     None,
    },
    "evaluation_stage": "watching",
    "additional_notes": "",
}


def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",  "sk-ant-test")
    monkeypatch.setenv("AR_SCOUT_MOCK_MODE", mock_mode)
    monkeypatch.setenv("DB_PATH",            str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",       "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",    str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",        str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


# ── mock mode tests ────────────────────────────────────────────────────────────

def test_assess_mock_mode_returns_200(monkeypatch, tmp_path):
    """Mock mode returns 200 without any Anthropic call."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text


def test_assess_mock_mode_response_structure(monkeypatch, tmp_path):
    """Mock response contains all required top-level fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["status"] == "ok"
    assert body["mock"] is True
    assert "assessment" in body
    assert "pillars" in body["assessment"]
    assert "composite" in body["assessment"]
    assert "verdict" in body["assessment"]
    assert "hard_gates" in body["assessment"]
    assert "career_ceiling" in body["assessment"]
    assert "risk_assessment" in body["assessment"]
    assert "five_year_test" in body["assessment"]
    assert "trajectory" in body["assessment"]
    assert "unfair_advantage" in body["assessment"]
    assert "remediation_priorities" in body["assessment"]


def test_assess_artist_identity_bound_from_payload(monkeypatch, tmp_path):
    """Artist name in response comes from request payload, not from profile."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["artist"] = dict(SAMPLE_PAYLOAD["artist"])
    payload["artist"]["name"] = "Payload Artist Name"

    resp = client.post("/api/agents/ar-scout/assess", json=payload)
    body = resp.json()

    assert body["artist"]["name"] == "Payload Artist Name"


def test_assess_all_five_pillars_present(monkeypatch, tmp_path):
    """Mock assessment includes all 5 pillar grades."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    pillars = resp.json()["assessment"]["pillars"]

    required_pillars = [
        "music_quality", "artist_identity", "audience_market",
        "execution_team", "commercial_opportunity",
    ]
    for pillar in required_pillars:
        assert pillar in pillars, f"Missing pillar: {pillar}"
        assert "grade" in pillars[pillar]
        assert "numeric" in pillars[pillar]
        assert "confidence" in pillars[pillar]


def test_assess_verdict_is_valid(monkeypatch, tmp_path):
    """Verdict is one of the six valid rubric verdicts."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    verdict = resp.json()["assessment"]["verdict"]

    valid_verdicts = {"PASS", "WATCH", "DEVELOP", "PURSUE", "GREENLIGHT", "SIGN IMMEDIATELY"}
    assert verdict in valid_verdicts, f"Invalid verdict: {verdict}"


def test_assess_composite_provisional(monkeypatch, tmp_path):
    """Composite is labeled PROVISIONAL per #12 lesson."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    composite = resp.json()["assessment"]["composite"]

    assert composite["label"] == "PROVISIONAL"
    assert "unlock_condition" in composite
    assert "30" in composite["unlock_condition"]


def test_assess_risk_assessment_all_eight_categories(monkeypatch, tmp_path):
    """Risk assessment covers all 8 required categories."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    risks = resp.json()["assessment"]["risk_assessment"]

    required_categories = [
        "execution", "financial", "reputation", "team",
        "legal", "burnout", "ai_displacement", "trend_dependency",
    ]
    for cat in required_categories:
        assert cat in risks, f"Missing risk category: {cat}"
        assert "level" in risks[cat]
        assert "reason" in risks[cat]
        assert risks[cat]["level"] in {"Low", "Medium", "High"}


def test_assess_five_year_test_present(monkeypatch, tmp_path):
    """Five-Year Test is present and has a non-empty answer."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    fyt = resp.json()["assessment"]["five_year_test"]

    assert "question" in fyt
    assert "answer" in fyt
    assert len(fyt["answer"]) > 0


def test_assess_no_probability_percentage_in_mock(monkeypatch, tmp_path):
    """Mock assessment must not contain probability percentage language."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    body_str = _json.dumps(resp.json()).lower()

    # Probability percentage patterns are forbidden until unlock condition
    import re
    prob_pattern = re.compile(r'\d+\s*%\s*(chance|probability|likelihood|shot)', re.I)
    matches = prob_pattern.findall(body_str)
    assert not matches, f"Forbidden probability language found: {matches}"


def test_assess_no_entity_strings_in_response(monkeypatch, tmp_path):
    """Assess JSON response must not contain forbidden provenance markers."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    assert_no_forbidden_terms(_json.dumps(resp.json()))


def test_assess_missing_required_field_returns_422(monkeypatch, tmp_path):
    """Missing required artist.name returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = dict(SAMPLE_PAYLOAD)
    bad_payload["artist"] = {"genre": "R&B"}  # missing name
    resp = client.post("/api/agents/ar-scout/assess", json=bad_payload)
    assert resp.status_code == 422


# ── no-key / live-mode fallback tests ─────────────────────────────────────────

def test_assess_no_anthropic_key_mock_mode_still_works(monkeypatch, tmp_path):
    """Without ANTHROPIC_API_KEY, mock mode still returns 200."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AR_SCOUT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_assess_live_mode_no_key_returns_503(monkeypatch, tmp_path):
    """Live mode without ANTHROPIC_API_KEY returns 503."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AR_SCOUT_MOCK_MODE", "false")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/ar-scout/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json().get("detail", "")
