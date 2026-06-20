"""
Tests for POST /api/agents/tour-commander/assess route.

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
    "artist_territory": "US",
    "campaign": {
        "campaign_name":                     "Spring Headline Run",
        "tour_type":                         "headline",
        "markets_count":                     14,
        "has_international_dates":            True,
        "anchor_dates_confirmed":            True,
        "routing_efficiency_ratio":          0.62,
        "dead_legs_analyzed":                True,
        "break_even_model_exists":           True,
        "modeled_before_routing":            True,
        "sensitivity_scenarios_modeled":     True,
        "offers_evaluated_against_framework": True,
        "split_points_analyzed":             True,
        "red_flag_clauses_identified":       True,
        "rider_complete":                    True,
        "production_advance_completed":      True,
        "advance_lead_weeks":                3,
        "price_points_market_analyzed":      False,
        "tier_structure_defined":            True,
        "secondary_market_monitored":        True,
        "work_permits_confirmed":            True,
        "withholding_modeled":               False,
        "territory_streaming_signal":        True,
        "merch_planned":                     True,
        "hall_fees_documented":              True,
        "settlement_review_process":         True,
        "red_flag_clauses":                  [],
    },
    "additional_notes": "",
}


def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",        "sk-ant-test")
    monkeypatch.setenv("TOUR_COMMANDER_MOCK_MODE", mock_mode)
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
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text


def test_assess_mock_mode_response_structure(monkeypatch, tmp_path):
    """Mock response contains all required top-level fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["status"] == "ok"
    assert body["mock"] is True
    assert "assessment" in body
    assert "dimensions" in body["assessment"]
    assert "composite" in body["assessment"]
    assert "hard_gates" in body["assessment"]
    assert "risk_classification" in body["assessment"]
    assert "next_best_action" in body["assessment"]
    assert "action_profile" in body["assessment"]


def test_assess_artist_identity_bound_from_payload(monkeypatch, tmp_path):
    """Artist name in response comes from request payload."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["artist_name"] = "Payload Artist Name"

    resp = client.post("/api/agents/tour-commander/assess", json=payload)
    body = resp.json()

    assert body["artist_name"] == "Payload Artist Name"


def test_assess_all_eight_dimensions_present(monkeypatch, tmp_path):
    """Mock assessment includes all 8 rubric dimensions with required fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    dimensions = resp.json()["assessment"]["dimensions"]

    required_dims = [
        "routing_logic", "financial_model_integrity",
        "offer_evaluation_quality", "production_readiness",
        "ticketing_strategy", "international_readiness",
        "merch_planning", "settlement_process",
    ]
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
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    dims = resp.json()["assessment"]["dimensions"]

    total = sum(dims[d]["weight"] for d in dims)
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"


def test_assess_all_four_hard_gates_present(monkeypatch, tmp_path):
    """Hard gates dict contains all four required gate keys."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]

    required_gates = [
        "break_even_gate", "anchor_dates_gate",
        "work_permit_gate", "production_advance_gate",
    ]
    for gate in required_gates:
        assert gate in gates, f"Missing hard gate: {gate}"


def test_assess_composite_provisional(monkeypatch, tmp_path):
    """Composite is labeled PROVISIONAL and has an unlock condition."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    composite = resp.json()["assessment"]["composite"]

    assert composite["label"] == "PROVISIONAL"
    assert "unlock_condition" in composite
    assert "30" in composite["unlock_condition"]


def test_assess_composite_value_in_range(monkeypatch, tmp_path):
    """Composite value is in the 0.0–4.3 range (letter-grade numeric scale)."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    value = resp.json()["assessment"]["composite"]["value"]

    assert 0.0 <= value <= 4.3, f"Composite value out of range: {value}"


def test_assess_risk_classification_is_valid(monkeypatch, tmp_path):
    """Risk classification is one of the five descriptive tiers."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    rc = resp.json()["assessment"]["risk_classification"]

    valid = {
        "LOW_RISK", "NOTABLE_GAPS", "SIGNIFICANT_GAPS",
        "HIGH_FINANCIAL_RISK", "CRITICAL_RISK",
    }
    assert rc in valid, f"Invalid risk classification: {rc}"


def test_assess_advisory_footer_present(monkeypatch, tmp_path):
    """Every assessment carries the operational-advisory disclaimer (not legal/tax/immigration advice)."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    assessment = resp.json()["assessment"]

    assert "advisory_footer" in assessment
    assert "not legal" in assessment["advisory_footer"].lower()


def test_assess_tour_type_bound_from_payload(monkeypatch, tmp_path):
    """Tour type from payload appears in the assessment block."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["campaign"] = dict(SAMPLE_PAYLOAD["campaign"])
    payload["campaign"]["tour_type"] = "festival_run"

    resp = client.post("/api/agents/tour-commander/assess", json=payload)
    body = resp.json()

    assert body["campaign"]["tour_type"] == "festival_run"
    assert body["assessment"]["tour_type"] == "festival_run"


def test_assess_template_not_mutated_across_requests(monkeypatch, tmp_path):
    """Per-request tour_type must not leak into the shared mock template."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")

    p1 = dict(SAMPLE_PAYLOAD)
    p1["campaign"] = dict(SAMPLE_PAYLOAD["campaign"]); p1["campaign"]["tour_type"] = "support"
    r1 = client.post("/api/agents/tour-commander/assess", json=p1).json()

    p2 = dict(SAMPLE_PAYLOAD)
    p2["campaign"] = dict(SAMPLE_PAYLOAD["campaign"]); p2["campaign"]["tour_type"] = "one_off"
    r2 = client.post("/api/agents/tour-commander/assess", json=p2).json()

    assert r1["assessment"]["tour_type"] == "support"
    assert r2["assessment"]["tour_type"] == "one_off"


def test_assess_campaign_fields_in_response(monkeypatch, tmp_path):
    """Campaign fields from payload appear in response."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["campaign"]["tour_type"] == "headline"
    assert body["campaign"]["markets_count"] == 14
    assert body["campaign"]["advance_lead_weeks"] == 3
    assert body["campaign"]["has_international_dates"] is True


def test_assess_no_entity_strings_in_response(monkeypatch, tmp_path):
    """Assess JSON response must not contain forbidden provenance markers."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    assert_no_forbidden_terms(_json.dumps(resp.json()))


def test_assess_missing_artist_name_returns_422(monkeypatch, tmp_path):
    """Missing required artist_name returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = dict(SAMPLE_PAYLOAD)
    del bad_payload["artist_name"]
    resp = client.post("/api/agents/tour-commander/assess", json=bad_payload)
    assert resp.status_code == 422


def test_assess_missing_campaign_returns_422(monkeypatch, tmp_path):
    """Missing required campaign returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = {k: v for k, v in SAMPLE_PAYLOAD.items() if k != "campaign"}
    resp = client.post("/api/agents/tour-commander/assess", json=bad_payload)
    assert resp.status_code == 422


def test_assess_action_profile_priorities_valid(monkeypatch, tmp_path):
    """Action profile entries use the four defined priority bands."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    profile = resp.json()["assessment"]["action_profile"]

    valid = {"IMMEDIATE", "PRIORITY", "OPTIMIZE", "MAINTAIN"}
    assert isinstance(profile, list) and len(profile) >= 1
    for entry in profile:
        assert entry["priority"] in valid, f"Invalid priority: {entry['priority']}"
        assert "item" in entry


# ── no-key / live-mode fallback tests ─────────────────────────────────────────

def test_assess_no_anthropic_key_mock_mode_still_works(monkeypatch, tmp_path):
    """Without ANTHROPIC_API_KEY, mock mode still returns 200."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("TOUR_COMMANDER_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_assess_live_mode_no_key_returns_503(monkeypatch, tmp_path):
    """Live mode without ANTHROPIC_API_KEY returns 503."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("TOUR_COMMANDER_MOCK_MODE", "false")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/tour-commander/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json().get("detail", "")
