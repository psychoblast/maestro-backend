"""
PROOF tests — tour_ops_data (Miles Unit 1, corpus only).

Asserts the structured tour-ops corpus faithfully encodes MILES_TOUR_OPS_MAP_v1:
  - module-level guarantees: data-only (no def/class/import/call),
    JSON-serializable throughout, entity-wall clean;
  - ZERO currency symbols or amounts anywhere — settlement and budget
    mechanisms are described as mechanisms ("a nightly guarantee", "a flat
    fee"), never as figures;
  - ADVANCING_DOCTRINE distinguishes venue advance vs production advance,
    lists what the venue provides, flags union-house labor rules as a budget
    risk, and states the parking "never risk being blocked in at load-out"
    doctrine;
  - DAY_SHEET_SPEC carries the minimum fields and flags hotel / door-code /
    flight fields sensitive (the actual exclusion logic is Unit 2's job —
    here only the flag is asserted);
  - SETTLEMENT_PREP_DOCTRINE names the ledger-lock boundary explicitly,
    the afternoon pre-settlement review timing, that a show can be left
    unsettled absent an immediate remedy, and the settlement vocabulary;
  - ROUTING_AND_PREP carries the routing-sheet fields and the advancing
    spreadsheet's dashboard status categories;
  - FESTIVAL_VARIANT carries the welcome-letter topics and the flat-fee +
    withholding settlement mechanism, with no numbers;
  - BOUNDARIES routes booking to venue-hawk ("after the deal memo" / "never
    renegotiates") and royalty/accounting to ledger-lock.
No service or main.py wiring exists yet at this unit; these tests import the
data module directly.
"""
import ast
import json
import pathlib
import re

import tour_ops_data as td
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "MILES_DOCTRINE", "ADVANCING_DOCTRINE", "DAY_SHEET_SPEC",
    "DAY_SHEET_VARIANTS", "SETTLEMENT_PREP_DOCTRINE", "SETTLEMENT_VOCABULARY",
    "ROUTING_AND_PREP", "FESTIVAL_VARIANT", "BOUNDARIES",
)

_SOURCE = pathlib.Path(td.__file__).read_text(encoding="utf-8")


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(td, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(td, name))  # raises TypeError on any leak


def test_module_is_data_only_no_def_class_or_import():
    tree = ast.parse(_SOURCE)
    for node in tree.body:
        assert isinstance(node, (ast.Expr, ast.Assign)), (
            f"non-data top-level node: {type(node).__name__}"
        )
        if isinstance(node, ast.Expr):
            assert isinstance(node.value, ast.Constant), "only the docstring may be an Expr"
    forbidden_nodes = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                       ast.Import, ast.ImportFrom, ast.Call)
    for node in ast.walk(tree):
        assert not isinstance(node, forbidden_nodes), (
            f"forbidden node anywhere in module: {type(node).__name__}"
        )


def test_no_forbidden_entity_wall_terms_in_source():
    assert_no_forbidden_terms(_SOURCE)


# ── ZERO currency amounts anywhere ─────────────────────────────────────────────

def test_no_currency_symbols_anywhere_in_source():
    for symbol in ("$", "£", "€", "¥", "₹", "¢", "₩"):
        assert symbol not in _SOURCE, f"currency symbol {symbol!r} leaked into the corpus"


def test_no_currency_amounts_in_serialized_corpus():
    # Scan the fully-serialized corpus for a number adjacent to any money word.
    blob = "\n".join(
        json.dumps(getattr(td, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    money_words = r"(?:dollars?|usd|cad|eur|euros?|gbp|pounds?|cents?|aud|fees?)"
    assert not re.search(rf"\d[\d,\.]*\s*{money_words}", blob), "digit-then-money-word amount found"
    assert not re.search(rf"{money_words}\s*\d", blob), "money-word-then-digit amount found"


def test_miles_doctrine_bans_dollar_figures():
    text = json.dumps(td.MILES_DOCTRINE).lower()
    assert "dollar figure" in text or "fee amount" in text or "guarantee amount" in text


# ── ADVANCING_DOCTRINE coverage ────────────────────────────────────────────────

_EXPECTED_ADVANCING_KEYS = {
    "advancing_overview", "advance_package_contents", "venue_advance",
    "production_advance", "parking_and_load_out",
}


def test_all_advancing_keys_present_with_schema():
    assert set(td.ADVANCING_DOCTRINE) == _EXPECTED_ADVANCING_KEYS
    for key, rec in td.ADVANCING_DOCTRINE.items():
        assert rec["key"] == key
        for field in ("topic", "description", "venue_provides",
                      "union_house_risk", "parking_doctrine"):
            assert field in rec, f"{key} missing {field}"
        assert isinstance(rec["venue_provides"], list)


def test_venue_advance_vs_production_advance_distinguished():
    venue = td.ADVANCING_DOCTRINE["venue_advance"]["description"].lower()
    production = td.ADVANCING_DOCTRINE["production_advance"]["description"].lower()
    assert "venue" in venue and "house" in venue
    assert "production" in production and "tech rider" in production
    assert venue != production


def test_venue_provides_list_present_on_venue_advance():
    provides = td.ADVANCING_DOCTRINE["venue_advance"]["venue_provides"]
    assert isinstance(provides, list) and provides
    joined = " ".join(provides).lower()
    assert "load-in" in joined
    assert "rigging" in joined
    assert "audio" in joined and "lighting" in joined


def test_union_house_labor_rule_flagged_as_budget_risk():
    risk = td.ADVANCING_DOCTRINE["venue_advance"]["union_house_risk"]
    assert risk is not None
    assert "union" in risk.lower()
    assert "budget risk" in risk.lower()


def test_parking_doctrine_mentions_blocked_in_at_load_out():
    parking_rec = td.ADVANCING_DOCTRINE["parking_and_load_out"]
    assert "blocked in" in parking_rec["parking_doctrine"].lower()
    assert "load-out" in parking_rec["parking_doctrine"].lower()
    assert "blocked in" in parking_rec["description"].lower()
    assert "premium" in parking_rec["description"].lower()


def test_advance_package_contents_names_the_bundle():
    text = td.ADVANCING_DOCTRINE["advance_package_contents"]["description"].lower()
    for item in ("tech rider", "stage plot", "input list", "hospitality rider",
                 "pass sheet", "settlement"):
        assert item in text, f"advance package missing {item!r}"


def test_advancing_overview_cross_refs_venue_hawk_for_contacts():
    text = td.ADVANCING_DOCTRINE["advancing_overview"]["description"].lower()
    assert "venue-hawk" in text
    assert "deal memo" in text


# ── DAY_SHEET_SPEC coverage + sensitive flag ───────────────────────────────────

_EXPECTED_DAY_SHEET_FIELDS = {
    "day", "date", "venue_name", "venue_address", "doors", "set_times",
    "set_lengths", "changeover", "curfew", "wifi", "artist_hotel_info",
    "door_codes", "flight_details",
}


def test_day_sheet_spec_has_minimum_fields():
    fields = {rec["field"] for rec in td.DAY_SHEET_SPEC}
    assert _EXPECTED_DAY_SHEET_FIELDS <= fields
    for rec in td.DAY_SHEET_SPEC:
        assert "field" in rec and "sensitive" in rec
        assert isinstance(rec["sensitive"], bool)


def test_hotel_door_code_flight_fields_flagged_sensitive():
    by_field = {rec["field"]: rec for rec in td.DAY_SHEET_SPEC}
    for field in ("artist_hotel_info", "door_codes", "flight_details"):
        assert by_field[field]["sensitive"] is True, f"{field} must be flagged sensitive"


def test_at_least_one_field_flagged_not_sensitive():
    by_field = {rec["field"]: rec for rec in td.DAY_SHEET_SPEC}
    for field in ("doors", "curfew"):
        assert by_field[field]["sensitive"] is False


def test_day_sheet_variants_document_principal_vs_crew():
    text = td.DAY_SHEET_VARIANTS["principal_vs_crew"].lower()
    assert "principal" in text and "crew" in text
    assert "omit" in text


# ── SETTLEMENT_PREP_DOCTRINE coverage ──────────────────────────────────────────

_EXPECTED_SETTLEMENT_KEYS = {
    "settlement_overview", "understand_the_deal_memo_before_the_tour",
    "confirm_the_deposit", "banking_info_sent_ahead",
    "pre_settlement_review_timing", "unsettled_is_sometimes_correct",
}


def test_all_settlement_keys_present_with_schema():
    assert set(td.SETTLEMENT_PREP_DOCTRINE) == _EXPECTED_SETTLEMENT_KEYS
    for key, rec in td.SETTLEMENT_PREP_DOCTRINE.items():
        assert rec["key"] == key
        assert rec.get("topic") and rec.get("description")


def test_settlement_names_ledger_lock_boundary_explicitly():
    text = td.SETTLEMENT_PREP_DOCTRINE["settlement_overview"]["description"].lower()
    assert "ledger-lock boundary" in text
    assert "prep only" in text


def test_pre_settlement_review_is_afternoon_of_show_day():
    text = td.SETTLEMENT_PREP_DOCTRINE["pre_settlement_review_timing"]["description"].lower()
    assert "afternoon" in text
    assert "show day" in text


def test_show_can_be_left_unsettled_when_no_immediate_remedy():
    text = td.SETTLEMENT_PREP_DOCTRINE["unsettled_is_sometimes_correct"]["description"].lower()
    assert "unsettled" in text
    assert "no immediate remedy" in text
    assert "not a failure state" in text


def test_deposit_confirmed_via_agency_report():
    text = td.SETTLEMENT_PREP_DOCTRINE["confirm_the_deposit"]["description"].lower()
    assert "deposit" in text and "agency report" in text


def test_banking_info_sent_ahead_of_time():
    text = td.SETTLEMENT_PREP_DOCTRINE["banking_info_sent_ahead"]["description"].lower()
    assert "w9" in text or "wire" in text
    assert "ahead" in text


_EXPECTED_SETTLEMENT_VOCAB_TERMS = {
    "sellable_vs_legal_capacity", "advance_vs_walk_up_pricing", "ticket_buys",
    "vip_settled_separately", "regional_withholding",
}


def test_settlement_vocabulary_present_with_schema():
    assert set(td.SETTLEMENT_VOCABULARY) == _EXPECTED_SETTLEMENT_VOCAB_TERMS
    for term, rec in td.SETTLEMENT_VOCABULARY.items():
        assert rec["term"] == term
        assert rec.get("mechanism")


def test_regional_withholding_cross_refs_ledger_lock():
    text = td.SETTLEMENT_VOCABULARY["regional_withholding"]["mechanism"].lower()
    assert "ledger-lock" in text


def test_vip_settled_separately_from_general_sales():
    text = td.SETTLEMENT_VOCABULARY["vip_settled_separately"]["mechanism"].lower()
    assert "separate" in text


# ── ROUTING_AND_PREP coverage ───────────────────────────────────────────────────

def test_routing_sheet_fields_present():
    rec = td.ROUTING_AND_PREP["routing_sheet_fields"]
    assert set(rec["fields"]) == {"date", "city", "venue", "drive_distance", "travel_method"}


def test_advancing_spreadsheet_dashboard_status_categories_present():
    rec = td.ROUTING_AND_PREP["advancing_spreadsheet_dashboard"]
    fields = rec["fields"]
    assert "sent_done_outstanding_status" in fields
    assert "hotels_status" in fields
    assert "flights_status" in fields
    assert "drive_times" in fields
    assert "time_zone_change_flag" in fields
    text = rec["description"].lower()
    assert "dashboard" in text
    assert "time zone" in text


# ── FESTIVAL_VARIANT coverage ───────────────────────────────────────────────────

def test_welcome_letter_topics_present():
    rec = td.FESTIVAL_VARIANT["welcome_letter_topics"]
    for topic in ("production", "parking", "hotels", "credentials", "comps",
                  "merch", "settlement", "deadlines"):
        assert topic in rec["fields"], f"welcome letter missing topic {topic!r}"
    assert "welcome letter" in rec["description"].lower()


def test_reconfirm_stage_set_time_before_deep_prep():
    text = td.FESTIVAL_VARIANT["reconfirm_before_deep_prep"]["description"].lower()
    assert "set time" in text and "set length" in text
    assert "reconfirm" in text


def test_festival_settlement_flat_fee_and_withholding_mechanism_no_numbers():
    rec = td.FESTIVAL_VARIANT["festival_settlement_mechanism"]
    text = rec["description"].lower()
    assert "flat fee" in text
    assert "withholding" in text
    assert "merch limit" in text
    assert not re.search(r"\d", text), "festival settlement mechanism must contain no numbers"


# ── BOUNDARIES coverage ─────────────────────────────────────────────────────────

_EXPECTED_BOUNDARY_ROUTES = {
    "booking_and_deal_terms": "venue-hawk",
    "royalty_and_accounting": "ledger-lock",
}


def test_boundaries_route_to_owning_departments():
    for key, dept in _EXPECTED_BOUNDARY_ROUTES.items():
        assert key in td.BOUNDARIES, f"missing boundary entry: {key}"
        rec = td.BOUNDARIES[key]
        assert rec["owning_department"] == dept, f"{key} routes to wrong department"
        assert rec.get("what") and rec.get("miles_role")


def test_booking_boundary_language_after_deal_memo_never_renegotiates():
    text = td.BOUNDARIES["booking_and_deal_terms"]["miles_role"].lower()
    assert "after the deal memo" in text
    assert "never renegotiates" in text


def test_royalty_boundary_routes_to_ledger_lock():
    rec = td.BOUNDARIES["royalty_and_accounting"]
    assert rec["owning_department"] == "ledger-lock"
    assert "ledger-lock" in rec["miles_role"].lower()
