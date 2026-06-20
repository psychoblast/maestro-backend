"""
Tests for POST /api/agents/ink-and-air/assess route.

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
        "pro_registration_complete":          True,
        "mechanical_registration_complete":   False,
        "new_works_registered_before_release": True,
        "active_income_streams":             ["performance", "mechanical", "ugc"],
        "ugc_monetization_active":           True,
        "neighboring_rights_registered":     False,
        "mlc_unmatched_claims_filed":        None,
        "black_box_claim_strategy":          False,
        "iswc_coverage_complete":            True,
        "ipi_registered_all_parties":        True,
        "active_revenue_without_identifiers": False,
        "split_sheets_executed":             True,
        "chain_of_title_documented":         True,
        "active_ownership_dispute":          False,
        "one_stop_clearance":                None,
        "sync_rep_in_place":                 False,
        "master_rights_clear":               True,
        "subpublishing_in_major_territories": True,
        "territories_collecting_count":      4,
        "statement_matching_rate":           0.88,
        "audit_window_status":               "within",
        "last_audit_within_window":          True,
        "active_litigation":                 False,
        "uncleared_sample_exposure":         None,
    },
    "additional_notes": "",
}


def _load_app(monkeypatch, tmp_path, *, mock_mode: str = "true"):
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("INK_AND_AIR_MOCK_MODE",  mock_mode)
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        return TestClient(m.app)


# ── mock mode tests ────────────────────────────────────────────────────────────

def test_assess_mock_mode_returns_200(monkeypatch, tmp_path):
    """Mock mode returns 200 without any Anthropic call."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200, resp.text


def test_assess_mock_mode_response_structure(monkeypatch, tmp_path):
    """Mock response contains all required top-level and assessment fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    body = resp.json()

    assert body["status"] == "ok"
    assert body["mock"] is True
    assert "assessment" in body
    a = body["assessment"]
    assert "dimensions" in a
    assert "composite" in a
    assert "hard_gates" in a
    assert "risk_classification" in a
    assert "action_profile" in a
    assert "asset_recovery_frame" in a
    assert "next_best_action" in a


def test_assess_artist_identity_bound_from_payload(monkeypatch, tmp_path):
    """Artist name in response comes from request payload, not an account profile."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["artist_name"] = "Payload Writer Name"

    resp = client.post("/api/agents/ink-and-air/assess", json=payload)
    assert resp.json()["artist_name"] == "Payload Writer Name"


def test_assess_all_ten_dimensions_present(monkeypatch, tmp_path):
    """Mock assessment includes all 10 rubric dimensions with required fields."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    dimensions = resp.json()["assessment"]["dimensions"]

    required_dims = [
        "registration_completeness", "collection_coverage",
        "royalty_recovery_readiness", "identifier_completeness",
        "ownership_clarity", "licensing_readiness",
        "territorial_coverage", "metadata_quality",
        "audit_status", "legal_exposure",
    ]
    assert len(dimensions) == 10
    for dim in required_dims:
        assert dim in dimensions, f"Missing dimension: {dim}"
        assert "grade" in dimensions[dim]
        assert "numeric" in dimensions[dim]
        assert "weight" in dimensions[dim]
        assert "rationale" in dimensions[dim]
        assert "confidence" in dimensions[dim]


def test_assess_dimension_weights_sum_to_one(monkeypatch, tmp_path):
    """The ten dimension weights must sum to 1.0."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    dims = resp.json()["assessment"]["dimensions"]

    total = sum(dims[d]["weight"] for d in dims)
    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"


def test_assess_all_four_hard_gates_present(monkeypatch, tmp_path):
    """Hard gates dict contains all four required gate keys."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]

    required_gates = [
        "identifier_gate", "ownership_dispute_gate",
        "audit_window_gate", "litigation_gate",
    ]
    for gate in required_gates:
        assert gate in gates, f"Missing hard gate: {gate}"


def test_assess_composite_provisional(monkeypatch, tmp_path):
    """Composite is labeled PROVISIONAL with an unlock condition referencing 30."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    composite = resp.json()["assessment"]["composite"]

    assert composite["label"] == "PROVISIONAL"
    assert "unlock_condition" in composite
    assert "30" in composite["unlock_condition"]


def test_assess_composite_value_in_range(monkeypatch, tmp_path):
    """Composite value is in the 0–10 range (letter-grade numeric scale)."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    value = resp.json()["assessment"]["composite"]["value"]
    assert 0 <= value <= 10, f"Composite value out of range: {value}"


def test_assess_composite_matches_weighted_sum(monkeypatch, tmp_path):
    """The stated composite value matches the weighted sum of dimension numerics."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    a = resp.json()["assessment"]
    computed = sum(d["numeric"] * d["weight"] for d in a["dimensions"].values())
    assert abs(computed - a["composite"]["value"]) < 0.05, (
        f"Composite {a['composite']['value']} != weighted sum {computed:.3f}"
    )


def test_assess_risk_classification_is_valid(monkeypatch, tmp_path):
    """Risk classification is one of the five descriptive severity tiers."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    rc = resp.json()["assessment"]["risk_classification"]

    valid = {
        "LOW_RISK", "NOTABLE_GAPS", "SIGNIFICANT_GAPS",
        "MATERIALLY_DEFICIENT", "CRITICALLY_DEFICIENT",
    }
    assert rc in valid, f"Invalid risk classification: {rc}"


def test_assess_advisory_footer_present(monkeypatch, tmp_path):
    """Every assessment routes execution out — the binding domain constraint."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    assessment = resp.json()["assessment"]

    assert "advisory_footer" in assessment
    footer = assessment["advisory_footer"].lower()
    assert "counsel" in footer


def test_assess_action_profile_tiers_present(monkeypatch, tmp_path):
    """Action Profile contains the four standard tiers."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    ap = resp.json()["assessment"]["action_profile"]

    for tier in ["immediate", "priority", "optimize", "maintain"]:
        assert tier in ap, f"Missing action tier: {tier}"


def test_assess_catalog_name_bound_from_payload(monkeypatch, tmp_path):
    """Catalog name from payload appears in the assessment block."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    payload = dict(SAMPLE_PAYLOAD)
    payload["catalog"] = dict(SAMPLE_PAYLOAD["catalog"])
    payload["catalog"]["catalog_name"] = "Renamed Catalog"

    resp = client.post("/api/agents/ink-and-air/assess", json=payload)
    body = resp.json()

    assert body["catalog"]["catalog_name"] == "Renamed Catalog"
    assert body["assessment"]["catalog_name"] == "Renamed Catalog"


def test_assess_template_not_mutated_across_requests(monkeypatch, tmp_path):
    """Per-request catalog_name must not leak into the shared mock template."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")

    p1 = dict(SAMPLE_PAYLOAD)
    p1["catalog"] = dict(SAMPLE_PAYLOAD["catalog"]); p1["catalog"]["catalog_name"] = "Catalog One"
    r1 = client.post("/api/agents/ink-and-air/assess", json=p1).json()

    p2 = dict(SAMPLE_PAYLOAD)
    p2["catalog"] = dict(SAMPLE_PAYLOAD["catalog"]); p2["catalog"]["catalog_name"] = "Catalog Two"
    r2 = client.post("/api/agents/ink-and-air/assess", json=p2).json()

    assert r1["assessment"]["catalog_name"] == "Catalog One"
    assert r2["assessment"]["catalog_name"] == "Catalog Two"


def test_assess_catalog_fields_in_response(monkeypatch, tmp_path):
    """Catalog fields from payload appear in the response."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    cat = resp.json()["catalog"]

    assert cat["work_count"] == 42
    assert cat["statement_matching_rate"] == 0.88
    assert cat["audit_window_status"] == "within"


def test_assess_no_entity_strings_in_response(monkeypatch, tmp_path):
    """Assess JSON response must not contain forbidden provenance markers."""
    import json as _json
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    assert_no_forbidden_terms(_json.dumps(resp.json()))


def test_assess_missing_artist_name_returns_422(monkeypatch, tmp_path):
    """Missing required artist_name returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = dict(SAMPLE_PAYLOAD)
    del bad_payload["artist_name"]
    resp = client.post("/api/agents/ink-and-air/assess", json=bad_payload)
    assert resp.status_code == 422


def test_assess_missing_catalog_returns_422(monkeypatch, tmp_path):
    """Missing required catalog returns 422 validation error."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    bad_payload = {k: v for k, v in SAMPLE_PAYLOAD.items() if k != "catalog"}
    resp = client.post("/api/agents/ink-and-air/assess", json=bad_payload)
    assert resp.status_code == 422


# ── no-key / live-mode fallback tests ─────────────────────────────────────────

def test_assess_no_anthropic_key_mock_mode_still_works(monkeypatch, tmp_path):
    """Without ANTHROPIC_API_KEY, mock mode still returns 200."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("INK_AND_AIR_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["mock"] is True


def test_assess_live_mode_no_key_returns_503(monkeypatch, tmp_path):
    """Live mode without ANTHROPIC_API_KEY returns 503."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("INK_AND_AIR_MOCK_MODE", "false")
    monkeypatch.setenv("DB_PATH",         str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",    "")
    monkeypatch.setenv("AUDIO_CACHE_DIR", str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",     str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
        client = TestClient(m.app)

    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 503
    assert "ANTHROPIC_API_KEY" in resp.json().get("detail", "")


def test_assess_hard_gates_all_clear_for_healthy_catalog(monkeypatch, tmp_path):
    """The sample (no disputes/litigation, identifiers present, window not expired)
    clears all four hard gates."""
    client = _load_app(monkeypatch, tmp_path, mock_mode="true")
    resp = client.post("/api/agents/ink-and-air/assess", json=SAMPLE_PAYLOAD)
    gates = resp.json()["assessment"]["hard_gates"]
    for key, text in gates.items():
        assert "CLEAR" in text, f"Gate {key} not CLEAR: {text}"
