"""
Tests for POST /api/agents/producer-connect/assess route.

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
    "artist_territory": "CA",
    "project": {
        "project_name":                  "Test Single",
        "project_scope":                 "single",
        "target_format":                 "streaming",
        "reference_tracks_count":        3,
        "creative_brief_signed":         False,
        "sonic_target_measurable":       True,
        "producer_selected":             True,
        "team_credits_genre_matched":    True,
        "rates_confirmed_in_writing":    False,
        "full_team_locked":              False,
        "demo_exists":                   True,
        "structure_locked":              True,
        "composition_locked":            True,
        "mix_stage":                     "in_progress",
        "measured_loudness_in_spec":     None,
        "true_peak_in_spec":             None,
        "format_conforms":               None,
        "stems_complete":                None,
        "qc_bounced":                    False,
        "budget_documented":             True,
        "phase_allocated":               True,
        "contingency_reserved":          True,
        "actuals_reconciled":            False,
        "stereo_master_present":         True,
        "isrc_assigned":                 True,
        "core_metadata_complete":        False,
        "credits_finalized":             False,
        "schedule_exists":               True,
        "team_availability_confirmed":   True,
        "release_date_buffer_weeks":     3,
        "deal_memos_executed":           True,
        "master_ownership_assigned":     True,
        "wfh_confirmed_session_players": None,
        "cowrite_flagged":               None,
    },
    "additional_notes": "",
}


def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",          "sk-ant-test")
    monkeypatch.setenv("PRODUCER_CONNECT_MOCK_MODE",  mock_mode)
    monkeypatch.setenv("DB_PATH",                    str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",               "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",            str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",                str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",         "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


# ── mock mode tests ────────────────────────────────────────────────────────────

def test_assess_mock_mode_returns_200(monkeypatch, tmp_path):
    """Mock mode returns 200 without any Anthropic call."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text


def test_assess_mock_mode_response_structure(monkeypatch, tmp_path):
    """Mock response contains all required top-level and assessment fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["status"] == "ok"
    assert body["mock"] is True
    assert "assessment" in body
    a = body["assessment"]
    assert "dimensions" in a
    assert "composite" in a
    assert "hard_gates" in a
    assert "readiness_band" in a
    assert "action_profile" in a
    assert "next_best_action" in a


def test_assess_artist_identity_bound_from_payload(monkeypatch, tmp_path):
    """Artist name in response comes from request payload, not an account profile."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["artist_name"] = "Payload Artist Name"

    resp = client.post("/api/agents/producer-connect/assess", json=payload)
    assert resp.json()["artist_name"] == "Payload Artist Name"


def test_assess_all_eight_dimensions_present(monkeypatch, tmp_path):
    """Mock assessment includes all 8 rubric dimensions with required fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    dimensions = resp.json()["assessment"]["dimensions"]

    required_dims = [
        "creative_direction_clarity", "producer_team_fit",
        "song_arrangement_readiness", "technical_quality_standards",
        "budget_discipline", "delivery_qc_completeness",
        "schedule_feasibility", "deal_ownership_structure",
    ]
    assert len(dimensions) == 8
    for dim in required_dims:
        assert dim in dimensions, f"Missing dimension: {dim}"
        assert "grade" in dimensions[dim]
        assert "numeric" in dimensions[dim]
        assert "weight" in dimensions[dim]
        assert "rationale" in dimensions[dim]
        assert "confidence" in dimensions[dim]


def test_assess_dimension_weights_sum_to_one(monkeypatch, tmp_path):
    """The eight dimension weights must sum to 1.0."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    dims = resp.json()["assessment"]["dimensions"]

    total = sum(dims[d]["weight"] for d in dims)
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"


def test_assess_both_hard_gates_present(monkeypatch, tmp_path):
    """Hard gates dict contains both required gate keys."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]

    for gate in ["technical_quality_gate", "delivery_qc_gate"]:
        assert gate in gates, f"Missing hard gate: {gate}"


def test_assess_hard_gates_clear_for_healthy_project(monkeypatch, tmp_path):
    """The sample (mix in progress, no QC bounce, no missing package element)
    clears both hard gates."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]
    for key, text in gates.items():
        assert "CLEAR" in text, f"Gate {key} not CLEAR: {text}"


def test_assess_composite_provisional(monkeypatch, tmp_path):
    """Composite is labeled PROVISIONAL with an unlock condition referencing 30."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    composite = resp.json()["assessment"]["composite"]

    assert composite["label"] == "PROVISIONAL"
    assert "unlock_condition" in composite
    assert "30" in composite["unlock_condition"]


def test_assess_composite_value_in_range(monkeypatch, tmp_path):
    """Composite value is in the 0–10 range (letter-grade numeric scale)."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    value = resp.json()["assessment"]["composite"]["value"]
    assert 0 <= value <= 10, f"Composite value out of range: {value}"


def test_assess_composite_matches_weighted_sum(monkeypatch, tmp_path):
    """The stated composite value matches the weighted sum of dimension numerics."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    a = resp.json()["assessment"]
    computed = sum(d["numeric"] * d["weight"] for d in a["dimensions"].values())
    assert abs(computed - a["composite"]["value"]) < 0.05, (
        f"Composite {a['composite']['value']} != weighted sum {computed:.3f}"
    )


def test_assess_readiness_band_is_valid(monkeypatch, tmp_path):
    """Readiness band is one of the four rubric output bands."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    band = resp.json()["assessment"]["readiness_band"]

    valid = {
        "GREEN_RELEASE_READY", "YELLOW_PROCEED_WITH_NAMED_GAPS",
        "AMBER_ADDRESS_GAPS", "RED_NOT_READY",
    }
    assert band in valid, f"Invalid readiness band: {band}"


def test_assess_advisory_footer_present(monkeypatch, tmp_path):
    """Every assessment routes execution out — the binding domain constraint."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    assessment = resp.json()["assessment"]

    assert "advisory_footer" in assessment
    footer = assessment["advisory_footer"].lower()
    assert "counsel" in footer
    assert "publishing" in footer
    assert "sync" in footer


def test_assess_action_profile_tiers_present(monkeypatch, tmp_path):
    """Action Profile contains the four standard tiers."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    ap = resp.json()["assessment"]["action_profile"]

    for tier in ["immediate", "priority", "optimize", "maintain"]:
        assert tier in ap, f"Missing action tier: {tier}"


def test_assess_project_name_bound_from_payload(monkeypatch, tmp_path):
    """Project name from payload appears in the assessment block."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["project"] = dict(SAMPLE_PAYLOAD["project"])
    payload["project"]["project_name"] = "Renamed Project"

    resp = client.post("/api/agents/producer-connect/assess", json=payload)
    body = resp.json()

    assert body["project"]["project_name"] == "Renamed Project"
    assert body["assessment"]["project_name"] == "Renamed Project"


def test_assess_template_not_mutated_across_requests(monkeypatch, tmp_path):
    """Per-request project_name must not leak into the shared mock template."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")

    p1 = dict(SAMPLE_PAYLOAD)
    p1["project"] = dict(SAMPLE_PAYLOAD["project"]); p1["project"]["project_name"] = "Project One"
    r1 = client.post("/api/agents/producer-connect/assess", json=p1).json()

    p2 = dict(SAMPLE_PAYLOAD)
    p2["project"] = dict(SAMPLE_PAYLOAD["project"]); p2["project"]["project_name"] = "Project Two"
    r2 = client.post("/api/agents/producer-connect/assess", json=p2).json()

    assert r1["assessment"]["project_name"] == "Project One"
    assert r2["assessment"]["project_name"] == "Project Two"


def test_assess_project_fields_in_response(monkeypatch, tmp_path):
    """Project fields from payload appear in the response."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    proj = resp.json()["project"]

    assert proj["reference_tracks_count"] == 3
    assert proj["mix_stage"] == "in_progress"
    assert proj["release_date_buffer_weeks"] == 3


def test_assess_no_entity_strings_in_response(monkeypatch, tmp_path):
    """Assess JSON response must not contain forbidden provenance markers."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    assert_no_forbidden_terms(_json.dumps(resp.json()))


def test_assess_missing_artist_name_returns_422(monkeypatch, tmp_path):
    """Missing required artist_name returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = dict(SAMPLE_PAYLOAD)
    del bad_payload["artist_name"]
    resp = client.post("/api/agents/producer-connect/assess", json=bad_payload)
    assert resp.status_code == 422


def test_assess_missing_project_returns_422(monkeypatch, tmp_path):
    """Missing required project returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = {k: v for k, v in SAMPLE_PAYLOAD.items() if k != "project"}
    resp = client.post("/api/agents/producer-connect/assess", json=bad_payload)
    assert resp.status_code == 422


# ── no-key / live-mode fallback tests ─────────────────────────────────────────

def test_assess_no_anthropic_key_mock_mode_still_works(monkeypatch, tmp_path):
    """Without ANTHROPIC_API_KEY, mock mode still returns 200."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("PRODUCER_CONNECT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_assess_live_mode_no_key_returns_503(monkeypatch, tmp_path):
    """Live mode without ANTHROPIC_API_KEY returns 503."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("PRODUCER_CONNECT_MOCK_MODE", "false")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/producer-connect/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json().get("detail", "")
