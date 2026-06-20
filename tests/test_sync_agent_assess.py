"""
Tests for POST /api/agents/sync-agent/assess route.

All tests use mocks only. No live Anthropic calls.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from entity_wall_terms import assert_no_forbidden_terms


# ── test fixtures ──────────────────────────────────────────────────────────────

SAMPLE_PAYLOAD = {
    "artist_name":      "Test Artist",
    "artist_territory": "Canada",
    "track": {
        "title":               "Sample Track",
        "genre":               "R&B",
        "clearance_status":    "CLEARED",
        "is_one_stop":         True,
        "has_stems":           True,
        "has_clean_version":   True,
        "duration_sec":        198.0,
        "bpm":                 96.0,
        "has_samples":         False,
        "has_explicit_lyrics": False,
    },
    "brief": {
        "project_type":         "tv",
        "scene_description":    "Emotional reunion scene, late evening, warm lighting",
        "budget_range":         "$5k-$15k",
        "deadline_days":        14,
        "territory":            "North America",
        "reference_tracks":     ["Artist A - Song X", "Artist B - Song Y"],
        "lyric_restrictions":   [],
        "exclusivity_required": False,
        "buyer_class":          "mid-tier",
    },
    "additional_notes": "",
}


def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",   "sk-ant-test")
    monkeypatch.setenv("SYNC_AGENT_MOCK_MODE", mock_mode)
    monkeypatch.setenv("DB_PATH",             str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",        "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",     str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",         str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",  "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


# ── mock mode tests ────────────────────────────────────────────────────────────

def test_assess_mock_mode_returns_200(monkeypatch, tmp_path):
    """Mock mode returns 200 without any Anthropic call."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text


def test_assess_mock_mode_response_structure(monkeypatch, tmp_path):
    """Mock response contains all required top-level fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["status"] == "ok"
    assert body["mock"] is True
    assert "assessment" in body
    assert "dimensions" in body["assessment"]
    assert "composite" in body["assessment"]
    assert "verdict" in body["assessment"]
    assert "hard_gates" in body["assessment"]
    assert "pitch_rationale" in body["assessment"]
    assert "next_action" in body["assessment"]


def test_assess_artist_identity_bound_from_payload(monkeypatch, tmp_path):
    """Artist name in response comes from request payload."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["artist_name"] = "Payload Artist Name"

    resp = client.post("/api/agents/sync-agent/assess", json=payload)
    body = resp.json()

    assert body["artist_name"] == "Payload Artist Name"


def test_assess_all_four_dimensions_present(monkeypatch, tmp_path):
    """Mock assessment includes all 4 rubric dimensions."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    dimensions = resp.json()["assessment"]["dimensions"]

    required_dims = [
        "brief_fit", "clearance_complexity",
        "turnaround_feasibility", "fee_tier",
    ]
    for dim in required_dims:
        assert dim in dimensions, f"Missing dimension: {dim}"
        assert "score" in dimensions[dim]
        assert "weight" in dimensions[dim]
        assert "rationale" in dimensions[dim]
        assert "confidence" in dimensions[dim]


def test_assess_dimension_weights_sum_to_one(monkeypatch, tmp_path):
    """The four dimension weights must sum to 1.0."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    dims = resp.json()["assessment"]["dimensions"]

    total = sum(dims[d]["weight"] for d in dims)
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"


def test_assess_verdict_is_valid(monkeypatch, tmp_path):
    """Verdict is one of the three valid rubric verdicts."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    verdict = resp.json()["assessment"]["verdict"]

    assert verdict in {"PITCH", "HOLD", "PASS"}, f"Invalid verdict: {verdict}"


def test_assess_composite_provisional(monkeypatch, tmp_path):
    """Composite is labeled PROVISIONAL and has an unlock condition."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    composite = resp.json()["assessment"]["composite"]

    assert composite["label"] == "PROVISIONAL"
    assert "unlock_condition" in composite
    assert "30" in composite["unlock_condition"]


def test_assess_composite_value_in_range(monkeypatch, tmp_path):
    """Composite value is in the 0–100 range."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    value = resp.json()["assessment"]["composite"]["value"]

    assert 0 <= value <= 100, f"Composite value out of range: {value}"


def test_assess_all_three_hard_gates_present(monkeypatch, tmp_path):
    """Hard gates dict contains all three required gate keys."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]

    required_gates = [
        "clearance_unknown_gate",
        "turnaround_gate",
        "brief_fit_gate",
    ]
    for gate in required_gates:
        assert gate in gates, f"Missing hard gate: {gate}"


def test_assess_track_fields_in_response(monkeypatch, tmp_path):
    """Track fields from payload appear in response."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["track"]["title"] == "Sample Track"
    assert body["track"]["genre"] == "R&B"
    assert body["track"]["clearance_status"] == "CLEARED"


def test_assess_no_entity_strings_in_response(monkeypatch, tmp_path):
    """Assess JSON response must not contain forbidden provenance markers."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    assert_no_forbidden_terms(_json.dumps(resp.json()))


def test_assess_missing_required_field_returns_422(monkeypatch, tmp_path):
    """Missing required artist_name returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = dict(SAMPLE_PAYLOAD)
    del bad_payload["artist_name"]
    resp = client.post("/api/agents/sync-agent/assess", json=bad_payload)
    assert resp.status_code == 422


def test_assess_missing_track_returns_422(monkeypatch, tmp_path):
    """Missing required track returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = {k: v for k, v in SAMPLE_PAYLOAD.items() if k != "track"}
    resp = client.post("/api/agents/sync-agent/assess", json=bad_payload)
    assert resp.status_code == 422


# ── no-key / live-mode fallback tests ─────────────────────────────────────────

def test_assess_no_anthropic_key_mock_mode_still_works(monkeypatch, tmp_path):
    """Without ANTHROPIC_API_KEY, mock mode still returns 200."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("SYNC_AGENT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_assess_live_mode_no_key_returns_503(monkeypatch, tmp_path):
    """Live mode without ANTHROPIC_API_KEY returns 503."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("SYNC_AGENT_MOCK_MODE", "false")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/sync-agent/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json().get("detail", "")
