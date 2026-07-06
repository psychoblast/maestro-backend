"""
PROOF tests — booking_data (Ray B Unit 1, corpus only).

Asserts the booking / live-touring doctrine corpus faithfully encodes the map:
the HOLD_SYSTEM mechanism (first-come pencils + challenge/confirm chain, windows
as verify-live notes, small-venue scope caveat), the DEAL_MECHANISMS structures
(flat guarantee / door split / versus / guarantee+bonus / guarantee+% after
split point) with the HARD net-definition doctrine and the pay-to-play red flag,
the DEAL_MEMO_SPEC and RIDER_SPEC minimum specs, the OUTREACH_DOCTRINE (routing +
avails + cadence), the AGENT_ECONOMICS notes (commission varies, no upfront fees,
live-revenue only), the OUT_OF_SCOPE boundaries (tour-commander / puppet-master /
airwave), and the section-honesty rules with stable ids — plus the module-level
guarantees: data-only (no def/class/import/call), JSON-serializable throughout,
entity-wall clean, and the Ray-B-SPECIFIC hard rule that NO currency amount
appears anywhere in source (a numeric scan enforces it). No service or main.py
wiring exists yet; these tests import the data module directly.
"""
import ast
import json
import pathlib
import re

import booking_data as bk
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = ("HOLD_SYSTEM", "DEAL_MECHANISMS", "DEAL_MEMO_SPEC",
                        "RIDER_SPEC", "OUTREACH_DOCTRINE", "AGENT_ECONOMICS",
                        "OUT_OF_SCOPE", "HONESTY_RULES")

_SOURCE = pathlib.Path(bk.__file__).read_text(encoding="utf-8")

# The currency scan targets the DATA VALUES, not the module docstring (which
# carries the RAY_B_BOOKING_MAP_v1 provenance date) or code comments. Serialize
# every constant and scan that text — the "no invented amount" contract is about
# what the corpus RETURNS.
_DATA_TEXT = json.dumps([getattr(bk, n) for n in _TOP_LEVEL_CONSTANTS],
                        ensure_ascii=False)


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(bk, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(bk, name))  # raises TypeError on any leak


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


# ── REQUIRED: zero currency amounts anywhere in the corpus ─────────────────────

def test_no_currency_amounts_anywhere():
    # The whole point of this corpus is that it never quotes a rate, guarantee, or
    # split figure. A '$' or any 3+-digit run would signal an invented amount. The
    # only digits that may appear are the small window/timing numbers (24-48, 14,
    # 6, 1, 2, 10-15).
    assert "$" not in _SOURCE, "no currency symbol may appear in the corpus"
    for run in re.findall(r"\d+", _DATA_TEXT):
        assert len(run) <= 2, f"suspicious numeric run (possible currency amount): {run}"


# ── HOLD_SYSTEM ────────────────────────────────────────────────────────────────

def test_hold_system_first_come_pencils_and_challenge_chain():
    hs = bk.HOLD_SYSTEM
    assert "first-come" in hs["distribution"].lower()
    assert "pencil" in hs["distribution"].lower()
    assert hs["hold_order"] == ("first", "second", "third")
    # challenge offers the date UP the chain in hold order
    assert "up" in hs["challenge"].lower()
    # windows are notes that VARY — never a standard
    assert "varies" in hs["challenge_response_window"].lower()
    assert "varies" in hs["unchallenged_window"].lower()
    assert "no official standard" in hs["unchallenged_window"].lower()


def test_hold_system_small_venue_scope_caveat():
    hs = bk.HOLD_SYSTEM
    scope = hs["scope_doctrine"].lower()
    assert "mid-to-large" in scope
    assert "small bars" in scope
    assert "never assume" in scope


# ── DEAL_MECHANISMS ────────────────────────────────────────────────────────────

def test_deal_mechanism_structures_complete_and_numberless():
    ids = [s["id"] for s in bk.DEAL_MECHANISMS["structures"]]
    assert ids == ["flat_guarantee", "door_split", "versus_deal",
                   "guarantee_plus_bonus",
                   "guarantee_plus_percentage_after_split_point"]
    # every structure note frames the figure as negotiated, never quoted
    for s in bk.DEAL_MECHANISMS["structures"]:
        assert "negotiated" in s["note"].lower()


def test_versus_deal_is_greater_of():
    v = next(s for s in bk.DEAL_MECHANISMS["structures"] if s["id"] == "versus_deal")
    assert "greater of" in v["note"].lower()


def test_net_definition_is_hard_doctrine():
    doc = bk.DEAL_MECHANISMS["net_definition_doctrine"].lower()
    assert "hard doctrine" in doc
    assert "net" in doc
    assert "dispute" in doc
    assert "deal memo" in doc


def test_pay_to_play_is_a_red_flag_and_merch_hall_fee_noted():
    flags = {f["id"]: f for f in bk.DEAL_MECHANISMS["red_flags"]}
    assert "pay_to_play" in flags
    assert "red flag" in flags["pay_to_play"]["note"].lower()
    assert "never recommended" in flags["pay_to_play"]["note"].lower()
    assert "merch_hall_fee" in flags
    assert "negotiable" in flags["merch_hall_fee"]["note"].lower()


# ── DEAL_MEMO_SPEC + RIDER_SPEC ────────────────────────────────────────────────

def test_deal_memo_minimum_fields_present():
    fields = set(bk.DEAL_MEMO_SPEC["minimum_fields"])
    for expected in ("artist_legal_and_performing_name", "date_venue_city",
                     "fee_structure_with_all_terms_defined",
                     "nbor_gbor_definition_with_specific_deductions",
                     "production_rider_reference", "radius_clause_terms",
                     "deposit_amount_and_payment_schedule",
                     "cancellation_and_force_majeure"):
        assert expected in fields, f"missing deal-memo field: {expected}"
    # radius clause note warns about stacking regional dates
    assert "before" in bk.DEAL_MEMO_SPEC["field_notes"]["radius_clause_terms"].lower()


def test_rider_spec_splits_hospitality_and_technical():
    r = bk.RIDER_SPEC
    assert "green room" in r["hospitality_rider"].lower()
    assert "stage plot" in r["technical_rider"].lower()
    assert "backline" in r["backline_note"].lower()
    assert "festival" in r["backline_note"].lower()


# ── OUTREACH_DOCTRINE ──────────────────────────────────────────────────────────

def test_outreach_doctrine_routing_avails_and_no_essay():
    od = bk.OUTREACH_DOCTRINE
    assert "no bio" in od["email_style"].lower()
    assert "essay" in od["email_style"].lower()
    assert "avails" in od["avails_term"].lower()
    assert "loop geographically" in od["routing_doctrine"].lower()
    assert "public calendar" in od["follow_up_cadence"].lower()


# ── AGENT_ECONOMICS ────────────────────────────────────────────────────────────

def test_agent_economics_all_notes_never_a_rule():
    ae = bk.AGENT_ECONOMICS
    assert "varies" in ae["commission_note"].lower()
    assert "never assert" in ae["commission_note"].lower()
    assert "never charge upfront" in ae["no_upfront_fees"].lower()
    scope = ae["scope_of_commission"].lower()
    assert "live revenue" in scope
    assert "never" in scope
    assert "publishing" in scope


# ── OUT_OF_SCOPE boundaries ────────────────────────────────────────────────────

def test_boundaries_present_and_route_to_right_owners():
    oos = bk.OUT_OF_SCOPE
    assert oos["tour_operations"]["owner"] == "tour-commander"
    assert oos["playlist_curator_outreach"]["owner"] == "puppet-master"
    assert oos["radio_dsp_promotion"]["owner"] == "airwave"
    for entry in oos.values():
        assert entry["reason"]  # every boundary carries a reason


# ── HONESTY_RULES ──────────────────────────────────────────────────────────────

def test_honesty_rules_ids_and_shape():
    ids = [r["id"] for r in bk.HONESTY_RULES]
    assert ids == ["never_fabricate_venues", "no_deal_figures_ever",
                   "deal_evaluation_is_structural", "holds_are_not_confirmations"]
    for r in bk.HONESTY_RULES:
        assert r["statement"] and r["allowed"] and r["forbidden"]


def test_never_fabricate_venues_rule_present():
    rule = next(r for r in bk.HONESTY_RULES if r["id"] == "never_fabricate_venues")
    assert "never" in rule["statement"].lower()
    assert "artist-supplied" in rule["statement"].lower()
    assert "venue name" in rule["forbidden"].lower()


def test_no_deal_figures_rule_present():
    rule = next(r for r in bk.HONESTY_RULES if r["id"] == "no_deal_figures_ever")
    assert "invented" in rule["statement"].lower()
    assert "negotiated" in rule["statement"].lower()
