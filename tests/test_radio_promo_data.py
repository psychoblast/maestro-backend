"""
PROOF tests — radio_promo_data (Solo Unit 1, corpus only).

Asserts the radio + DSP-editorial promo corpus faithfully encodes the map:
college/community radio (the NACC Top-200 mechanics with 1-5 station weights and
the Going For Adds DB; the Canadian Earshot counterpart; the ~4+ week,
phone-driven campaign shape), the CanCon rule (35% commercial / 50% CBC — the
ONLY quota percentages, enforced by a numeric scan) and the MAPL points with the
NEVER-assert-status honesty rule, the honest commercial-radio barrier, DSP
editorial (Spotify window/via/copy with no-guarantee doctrine), the ADDENDUM
delivery layer (SERVICING_PLATFORMS with None costs, the delivery-vs-outreach
doctrine, the earshot -> FACTOR -> Jade cross-ref, satellite/public), and the
OUT_OF_SCOPE boundary (playlist-CURATOR outreach belongs to Marcus) — plus the
module-level guarantees: data-only (no def/class/import/call), JSON-serializable
throughout, entity-wall clean, and NO currency amount anywhere. These tests
import the data module directly; no service/main.py wiring exists yet.
"""
import ast
import json
import pathlib
import re

import radio_promo_data as rp
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = ("COLLEGE_RADIO", "CANCON", "COMMERCIAL_RADIO",
                        "DSP_EDITORIAL", "SERVICING_PLATFORMS",
                        "DELIVERY_VS_OUTREACH_DOCTRINE", "SATELLITE_AND_PUBLIC",
                        "OUT_OF_SCOPE", "HONESTY_RULES")

_SOURCE = pathlib.Path(rp.__file__).read_text(encoding="utf-8")


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(rp, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(rp, name))


def test_module_is_data_only_no_def_class_or_import():
    tree = ast.parse(_SOURCE)
    for node in tree.body:
        assert isinstance(node, (ast.Expr, ast.Assign)), (
            f"non-data top-level node: {type(node).__name__}")
        if isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Constant), "only the docstring may be an Expr"
    forbidden_nodes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                       ast.Import, ast.ImportFrom, ast.Call)
    for node in ast.walk(tree):
        assert not isinstance(node, forbidden_nodes), (
            f"forbidden node anywhere in module: {type(node).__name__}")


def test_no_forbidden_entity_wall_terms_in_source():
    assert_no_forbidden_terms(_SOURCE)


# ── REQUIRED: 35 / 50 are the only quota percentages; no currency anywhere ─────

def test_only_35_and_50_quota_numerics():
    pct = {m for m in re.findall(r"(\d+)\s*%", _SOURCE)}
    assert pct == {"35", "50"}, f"unexpected quota percentages: {pct}"


def test_no_currency_amounts_anywhere():
    assert "$" not in _SOURCE, "no currency symbol may appear — platform costs are None"


# ── REQUIRED: OUT_OF_SCOPE curator boundary belongs to Marcus ──────────────────

def test_out_of_scope_curator_entry_present_and_owned_by_marcus():
    oos = rp.OUT_OF_SCOPE
    assert "playlist_curator_outreach" in oos
    entry = oos["playlist_curator_outreach"]
    assert "marcus" in entry["owner"].lower()
    assert "management" in entry["owner"].lower()
    assert "boundary" in entry["reason"].lower()
    assert "curator" in entry["reason"].lower()


# ── REQUIRED: never-assert-MAPL honesty rule ───────────────────────────────────

def test_never_assert_mapl_rule_present():
    ids = [r["id"] for r in rp.HONESTY_RULES]
    assert "never_assert_mapl" in ids
    rule = next(r for r in rp.HONESTY_RULES if r["id"] == "never_assert_mapl")
    assert "never" in rule["statement"].lower()
    assert "licence" in rule["statement"].lower() or "license" in rule["statement"].lower()
    # also carried on the CanCon record itself
    assert "never" in rp.CANCON["honesty"]["rule"].lower()


# ── COLLEGE_RADIO / CANCON / COMMERCIAL / DSP structural coverage ──────────────

def test_college_radio_nacc_and_earshot():
    cr = rp.COLLEGE_RADIO
    assert "college & community" in cr["nacc"]["name"].lower()
    assert "1-5" in cr["nacc"]["station_weight_note"]
    assert "going for adds" in cr["nacc"]["adds_db"].lower()
    assert "earshot" in cr["earshot"]["name"].lower()
    assert "phone" in cr["campaign_shape"]["followup"].lower()


def test_cancon_mapl_four_points_and_declaration_passthrough():
    mapl = rp.CANCON["mapl"]
    for letter in ("m", "a", "p", "l"):
        assert mapl[letter], f"missing MAPL point: {letter}"
    assert "2 of the 4" in mapl["qualifies"] or "any 2" in mapl["qualifies"].lower()
    assert "declares" in mapl["declaration"].lower()
    assert "never computed" in mapl["declaration"].lower()
    # the quota rule carries both the commercial and CBC figures
    assert "35%" in rp.CANCON["rule"]["commercial_popular_music"]
    assert "50%" in rp.CANCON["rule"]["cbc"]


def test_commercial_radio_is_honest_context_not_a_service():
    cr = rp.COMMERCIAL_RADIO
    assert "not a service" in cr["barrier_note"].lower()


def test_dsp_editorial_window_via_copy_and_no_guarantees():
    dsp = rp.DSP_EDITORIAL
    assert "7 days" in dsp["spotify"]["window"]
    assert "spotify for artists" in dsp["spotify"]["via"].lower()
    assert "unreleased" in dsp["spotify"]["via"].lower()
    assert "'pop' tells an editor nothing" in dsp["spotify"]["copy"].lower()
    assert "consideration" in dsp["doctrine"]["no_guarantees"].lower()
    assert "never" in dsp["doctrine"]["no_guarantees"].lower()


# ── ADDENDUM (+3): servicing platforms, delivery-vs-outreach, FACTOR cross-ref ─

def test_servicing_platforms_records_complete_with_none_costs():
    sp = rp.SERVICING_PLATFORMS
    for key in ("yangaroo_dmds", "play_mpe", "earshot_distro", "mmd_note"):
        assert key in sp, f"missing servicing platform: {key}"
    # every priced platform keeps its cost as None + verify-live (never a figure)
    for key in ("yangaroo_dmds", "play_mpe", "earshot_distro"):
        assert sp[key]["costs"] is None, key
        assert "verify live" in sp[key]["costs_note"].lower(), key
    assert "vancouver" in sp["play_mpe"]["company"].lower()


def test_delivery_vs_outreach_doctrine_present():
    rule = rp.DELIVERY_VS_OUTREACH_DOCTRINE["rule"].lower()
    assert "deliver" in rule
    assert "guarantee" in rule
    assert "delivery = airplay" in rule  # he never claims delivery == airplay


def test_earshot_factor_jade_cross_ref_present():
    factor = rp.SERVICING_PLATFORMS["earshot_distro"]["factor_link"].lower()
    assert "factor" in factor
    assert "jade" in factor
    assert "grant" in factor


def test_satellite_and_public_siriusxm_and_cbc():
    sap = rp.SATELLITE_AND_PUBLIC
    assert "satellite" in sap["siriusxm"]["note"].lower()
    assert "dmds" in sap["siriusxm"]["note"].lower()
    assert "50% cancon" in sap["cbc"]["note"].lower()
    assert sap["cbc"]["submission_mechanism"] is None


# ── HONESTY_RULES ──────────────────────────────────────────────────────────────

def test_honesty_rules_ids_and_shape():
    ids = [r["id"] for r in rp.HONESTY_RULES]
    assert ids == ["never_assert_mapl", "no_placement_guarantees",
                   "costs_and_panel_sizes_verify_live",
                   "platform_costs_and_processes_verify_live",
                   "facts_supplied_or_marked"]
    for r in rp.HONESTY_RULES:
        assert r["statement"] and r["allowed"] and r["forbidden"]


def test_no_placement_guarantee_rule_present():
    rule = next(r for r in rp.HONESTY_RULES if r["id"] == "no_placement_guarantees")
    assert "consideration" in rule["statement"].lower()
    assert "never" in rule["statement"].lower()
