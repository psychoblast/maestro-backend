"""
Tests for POST /api/agents/grid-prophet/assess route.

All tests use mocks only. No live Anthropic calls.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from entity_wall_terms import assert_no_forbidden_terms


# ── test fixtures ──────────────────────────────────────────────────────────────

SAMPLE_PAYLOAD = {
    "artist": {
        "name":             "Test Artist",
        "genre":            "Pop",
        "stage":            "emerging",
        "territory":        "Canada",
        "monthly_listeners": 22000,
        "social_following":  8500,
        "save_rate":         0.058,
        "release_count":     2,
        "has_email_list":    True,
        "email_list_size":   640,
        "has_merch":         False,
        "prior_editorial_placements": 0,
    },
    "campaign": {
        "release_title":          "Test Single",
        "release_date":           "2026-08-15",
        "campaign_budget_usd":    1500.0,
        "campaign_window_weeks":  12,
        "primary_platforms":      ["tiktok", "instagram", "spotify"],
        "has_tour_dates":         False,
        "tour_territory":         None,
        "is_catalog_campaign":    False,
    },
    "additional_notes": "",
}


def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",       "sk-ant-test")
    monkeypatch.setenv("AR_SCOUT_MOCK_MODE",       "true")
    monkeypatch.setenv("GRID_PROPHET_MOCK_MODE",   mock_mode)
    monkeypatch.setenv("DB_PATH",                  str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",             "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",          str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",              str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",       "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


# ── mock mode tests ────────────────────────────────────────────────────────────

def test_assess_mock_mode_returns_200(monkeypatch, tmp_path):
    """Mock mode returns 200 without any Anthropic call."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text


def test_assess_mock_mode_response_structure(monkeypatch, tmp_path):
    """Mock response contains all required top-level fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["status"] == "ok"
    assert body["mock"] is True
    assert "assessment" in body
    assert "dimensions" in body["assessment"]
    assert "composite" in body["assessment"]
    assert "band" in body["assessment"]
    assert "hard_gates" in body["assessment"]
    assert "campaign_priorities" in body["assessment"]
    assert "channel_mix_recommendation" in body["assessment"]


def test_assess_all_eight_dimensions_present(monkeypatch, tmp_path):
    """Mock assessment includes all 8 rubric dimensions."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    dimensions = resp.json()["assessment"]["dimensions"]

    required = [
        "virality", "ugc_potential", "platform_fit", "editorial_readiness",
        "touring_synergy", "merch_d2c", "brand_partnership", "fan_ltv",
    ]
    for dim in required:
        assert dim in dimensions, f"Missing dimension: {dim}"
        assert "score" in dimensions[dim]
        assert "weight" in dimensions[dim]
        assert "confidence" in dimensions[dim]


def test_assess_composite_is_provisional(monkeypatch, tmp_path):
    """Composite is labeled PROVISIONAL until unlock condition is met."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    composite = resp.json()["assessment"]["composite"]

    assert composite["label"] == "PROVISIONAL"
    assert "unlock_condition" in composite
    assert "30" in composite["unlock_condition"]


def test_assess_band_is_valid(monkeypatch, tmp_path):
    """Band is one of the four valid output bands."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    band = resp.json()["assessment"]["band"]

    valid_bands = {"Green", "Yellow", "Amber", "Red"}
    assert band in valid_bands, f"Invalid band: {band}"


def test_assess_hard_gates_all_present(monkeypatch, tmp_path):
    """All three hard gates are present in the response."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]

    assert "editorial_gate" in gates
    assert "paid_spend_gate" in gates
    assert "brand_pitch_gate" in gates


def test_assess_artist_identity_bound_from_payload(monkeypatch, tmp_path):
    """Artist name in response comes from request payload, not from profile."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["artist"] = dict(SAMPLE_PAYLOAD["artist"])
    payload["artist"]["name"] = "Payload Artist Name"

    resp = client.post("/api/agents/grid-prophet/assess", json=payload)
    body = resp.json()

    assert body["artist"]["name"] == "Payload Artist Name"


def test_assess_campaign_data_round_trips(monkeypatch, tmp_path):
    """Campaign data from request is returned in the response body."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["campaign"]["release_title"] == "Test Single"
    assert body["campaign"]["campaign_window_weeks"] == 12


def test_assess_composite_weights_sum_to_one(monkeypatch, tmp_path):
    """Dimension weights in the mock response sum to 1.0."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    dims = resp.json()["assessment"]["dimensions"]

    total_weight = sum(d["weight"] for d in dims.values())
    assert abs(total_weight - 1.0) < 0.001, f"Weights sum to {total_weight}, expected 1.0"


def test_assess_composite_value_in_range(monkeypatch, tmp_path):
    """Composite score is between 1.0 and 10.0."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    value = resp.json()["assessment"]["composite"]["value"]

    assert 1.0 <= value <= 10.0, f"Composite {value} out of expected range"


def test_assess_campaign_priorities_not_empty(monkeypatch, tmp_path):
    """campaign_priorities list must not be empty."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    priorities = resp.json()["assessment"]["campaign_priorities"]

    assert isinstance(priorities, list)
    assert len(priorities) > 0


def test_assess_no_entity_strings_in_response(monkeypatch, tmp_path):
    """Assess JSON response must not contain forbidden provenance markers."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    assert_no_forbidden_terms(_json.dumps(resp.json()))


def test_assess_missing_required_field_returns_422(monkeypatch, tmp_path):
    """Missing required artist.name returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = dict(SAMPLE_PAYLOAD)
    bad_payload["artist"] = {"genre": "Pop"}  # missing name
    resp = client.post("/api/agents/grid-prophet/assess", json=bad_payload)
    assert resp.status_code == 422


def test_assess_missing_campaign_returns_422(monkeypatch, tmp_path):
    """Missing required campaign block returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = {"artist": SAMPLE_PAYLOAD["artist"]}  # missing campaign
    resp = client.post("/api/agents/grid-prophet/assess", json=bad_payload)
    assert resp.status_code == 422


# ── no-key / live-mode fallback tests ─────────────────────────────────────────

def test_assess_no_anthropic_key_mock_mode_still_works(monkeypatch, tmp_path):
    """Without ANTHROPIC_API_KEY, mock mode still returns 200."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AR_SCOUT_MOCK_MODE",     "true")
    monkeypatch.setenv("GRID_PROPHET_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_assess_live_mode_no_key_returns_503(monkeypatch, tmp_path):
    """Live mode without ANTHROPIC_API_KEY returns 503."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AR_SCOUT_MOCK_MODE",     "true")
    monkeypatch.setenv("GRID_PROPHET_MOCK_MODE", "false")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/grid-prophet/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json().get("detail", "")
