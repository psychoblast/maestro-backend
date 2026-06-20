"""
Tests for POST /api/agents/royalty-doctor/assess route.

All tests use mocks only. No live Anthropic calls.
"""
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from entity_wall_terms import assert_no_forbidden_terms


# ── test fixtures ──────────────────────────────────────────────────────────────

SAMPLE_PAYLOAD = {
    "artist_name":      "Test Writer",
    "artist_territory": "US",
    "catalog": {
        "catalog_name":                       "Test Catalog",
        "work_count":                         42,
        "has_international_usage":            True,
        "statement_data_available":          True,
        "registration_export_available":     True,
        "pro_registration_complete":          True,
        "mechanical_registration_complete":   False,
        "neighboring_rights_registered":     False,
        "identifiers_complete":              True,
        "active_revenue_without_identifiers": False,
        "statements_verified_against_dsp":   False,
        "anomaly_review_practiced":          False,
        "reserve_deductions_reviewed":       False,
        "unmatched_pool_claims_filed":       None,
        "black_box_program_active":          False,
        "proof_of_ownership_ready":          True,
        "active_income_streams":             ["master", "performance", "mechanical"],
        "audit_window_status":               "within",
        "statement_history_retained":        True,
        "soft_audit_practice":               True,
        "lag_vs_missing_tracked":            True,
        "chain_of_title_documented":         True,
        "split_sheets_executed":             False,
    },
    "additional_notes": "",
}


def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",        "sk-ant-test")
    monkeypatch.setenv("ROYALTY_DOCTOR_MOCK_MODE", mock_mode)
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
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text


def test_assess_mock_mode_response_structure(monkeypatch, tmp_path):
    """Mock response contains all required top-level and assessment fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["status"] == "ok"
    assert body["mock"] is True
    assert "assessment" in body
    a = body["assessment"]
    assert "dimensions" in a
    assert "composite" in a
    assert "hard_gates" in a
    assert "recovery_posture" in a
    assert "recovery_plan" in a
    assert "leak_map" in a
    assert "next_best_action" in a


def test_assess_artist_identity_bound_from_payload(monkeypatch, tmp_path):
    """Artist name in response comes from request payload, not an account profile."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["artist_name"] = "Payload Writer Name"

    resp = client.post("/api/agents/royalty-doctor/assess", json=payload)
    assert resp.json()["artist_name"] == "Payload Writer Name"


def test_assess_all_seven_dimensions_present(monkeypatch, tmp_path):
    """Mock assessment includes all 7 rubric dimensions with required fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    dimensions = resp.json()["assessment"]["dimensions"]

    required_dims = [
        "registration_integrity", "statement_verification",
        "black_box_recovery_readiness", "pipeline_coverage",
        "audit_readiness", "collection_timing_discipline",
        "recovery_documentation",
    ]
    assert len(dimensions) == 7
    for dim in required_dims:
        assert dim in dimensions, f"Missing dimension: {dim}"
        assert "grade" in dimensions[dim]
        assert "numeric" in dimensions[dim]
        assert "weight" in dimensions[dim]
        assert "rationale" in dimensions[dim]
        assert "confidence" in dimensions[dim]


def test_assess_dimension_weights_sum_to_one(monkeypatch, tmp_path):
    """The seven dimension weights must sum to 1.0."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    dims = resp.json()["assessment"]["dimensions"]

    total = sum(dims[d]["weight"] for d in dims)
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"


def test_assess_all_four_hard_gates_present(monkeypatch, tmp_path):
    """Hard gates dict contains all four required gate keys."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]

    required_gates = [
        "data_sufficiency_gate", "fabrication_gate",
        "lag_diagnosis_gate", "audit_window_gate",
    ]
    for gate in required_gates:
        assert gate in gates, f"Missing hard gate: {gate}"


def test_assess_composite_provisional(monkeypatch, tmp_path):
    """Composite is labeled PROVISIONAL with an unlock condition referencing 30."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    composite = resp.json()["assessment"]["composite"]

    assert composite["label"] == "PROVISIONAL"
    assert "unlock_condition" in composite
    assert "30" in composite["unlock_condition"]


def test_assess_composite_value_in_range(monkeypatch, tmp_path):
    """Composite value is in the 0–10 range (letter-grade numeric scale)."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    value = resp.json()["assessment"]["composite"]["value"]
    assert 0 <= value <= 10, f"Composite value out of range: {value}"


def test_assess_composite_matches_weighted_sum(monkeypatch, tmp_path):
    """The stated composite value matches the weighted sum of dimension numerics."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    a = resp.json()["assessment"]
    computed = sum(d["numeric"] * d["weight"] for d in a["dimensions"].values())
    assert abs(computed - a["composite"]["value"]) < 0.05, (
        f"Composite {a['composite']['value']} != weighted sum {computed:.3f}"
    )


def test_assess_recovery_posture_is_valid(monkeypatch, tmp_path):
    """Recovery posture is one of the five descriptive leakage tiers."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    rp = resp.json()["assessment"]["recovery_posture"]

    valid = {
        "FULLY_COLLECTING", "MINOR_LEAKAGE", "NOTABLE_LEAKAGE",
        "SIGNIFICANT_LEAKAGE", "SEVERE_LEAKAGE",
    }
    assert rp in valid, f"Invalid recovery posture: {rp}"


def test_assess_advisory_footer_present(monkeypatch, tmp_path):
    """Every assessment routes execution out — the binding domain constraint."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    assessment = resp.json()["assessment"]

    assert "advisory_footer" in assessment
    footer = assessment["advisory_footer"].lower()
    assert "counsel" in footer


def test_assess_recovery_plan_tiers_present(monkeypatch, tmp_path):
    """Recovery Plan contains the four standard tiers."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    rp = resp.json()["assessment"]["recovery_plan"]

    for tier in ["immediate", "priority", "optimize", "maintain"]:
        assert tier in rp, f"Missing recovery-plan tier: {tier}"


def test_assess_leak_map_entries_have_evidence(monkeypatch, tmp_path):
    """Each leak-map entry carries an evidence basis and a recoverable label."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    leak_map = resp.json()["assessment"]["leak_map"]

    assert isinstance(leak_map, list) and len(leak_map) >= 1
    for entry in leak_map:
        assert "leak" in entry
        assert "evidence" in entry
        assert "recoverable" in entry


def test_assess_catalog_name_bound_from_payload(monkeypatch, tmp_path):
    """Catalog name from payload appears in the assessment block."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["catalog"] = dict(SAMPLE_PAYLOAD["catalog"])
    payload["catalog"]["catalog_name"] = "Renamed Catalog"

    resp = client.post("/api/agents/royalty-doctor/assess", json=payload)
    body = resp.json()

    assert body["catalog"]["catalog_name"] == "Renamed Catalog"
    assert body["assessment"]["catalog_name"] == "Renamed Catalog"


def test_assess_template_not_mutated_across_requests(monkeypatch, tmp_path):
    """Per-request catalog_name must not leak into the shared mock template."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")

    p1 = dict(SAMPLE_PAYLOAD)
    p1["catalog"] = dict(SAMPLE_PAYLOAD["catalog"]); p1["catalog"]["catalog_name"] = "Catalog One"
    r1 = client.post("/api/agents/royalty-doctor/assess", json=p1).json()

    p2 = dict(SAMPLE_PAYLOAD)
    p2["catalog"] = dict(SAMPLE_PAYLOAD["catalog"]); p2["catalog"]["catalog_name"] = "Catalog Two"
    r2 = client.post("/api/agents/royalty-doctor/assess", json=p2).json()

    assert r1["assessment"]["catalog_name"] == "Catalog One"
    assert r2["assessment"]["catalog_name"] == "Catalog Two"


def test_assess_catalog_fields_in_response(monkeypatch, tmp_path):
    """Catalog fields from payload appear in the response."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    cat = resp.json()["catalog"]

    assert cat["work_count"] == 42
    assert cat["audit_window_status"] == "within"
    assert cat["active_income_streams"] == ["master", "performance", "mechanical"]


def test_assess_no_entity_strings_in_response(monkeypatch, tmp_path):
    """Assess JSON response must not contain forbidden provenance markers."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    assert_no_forbidden_terms(_json.dumps(resp.json()))


def test_assess_recoverable_amounts_not_estimable(monkeypatch, tmp_path):
    """Recoverable amounts in the priority plan must be labeled NOT ESTIMABLE
    when no statement history / dated gap range supports a figure."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    priority = resp.json()["assessment"]["recovery_plan"]["priority"]

    est = [p.get("estimated_recovery", "") for p in priority if "estimated_recovery" in p]
    assert est, "Expected at least one priority action with an estimated_recovery field"
    assert any("NOT ESTIMABLE" in e for e in est)


def test_assess_missing_artist_name_returns_422(monkeypatch, tmp_path):
    """Missing required artist_name returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = dict(SAMPLE_PAYLOAD)
    del bad_payload["artist_name"]
    resp = client.post("/api/agents/royalty-doctor/assess", json=bad_payload)
    assert resp.status_code == 422


def test_assess_missing_catalog_returns_422(monkeypatch, tmp_path):
    """Missing required catalog returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = {k: v for k, v in SAMPLE_PAYLOAD.items() if k != "catalog"}
    resp = client.post("/api/agents/royalty-doctor/assess", json=bad_payload)
    assert resp.status_code == 422


# ── no-key / live-mode fallback tests ─────────────────────────────────────────

def test_assess_no_anthropic_key_mock_mode_still_works(monkeypatch, tmp_path):
    """Without ANTHROPIC_API_KEY, mock mode still returns 200."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ROYALTY_DOCTOR_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_assess_live_mode_no_key_returns_503(monkeypatch, tmp_path):
    """Live mode without ANTHROPIC_API_KEY returns 503."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ROYALTY_DOCTOR_MOCK_MODE", "false")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json().get("detail", "")


def test_assess_all_gates_clear_for_healthy_catalog(monkeypatch, tmp_path):
    """The sample (data available, window within, lag tracked) clears all four
    hard gates."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/royalty-doctor/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]
    for key, text in gates.items():
        assert "CLEAR" in text, f"Gate {key} not CLEAR: {text}"
