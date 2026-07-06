"""
PROOF tests — legal_data (Lex Unit 1, corpus only).

Asserts the structured legal-education corpus faithfully encodes LEX_LEGAL_MAP_v1
and permanently locks THE ONE RULE ABOVE ALL at the data layer:
  - module-level guarantees: data-only (no def/class/import/call),
    JSON-serializable throughout, entity-wall clean;
  - ZERO currency symbols or amounts anywhere — including lawyer fees, which are
    encoded as "a few hours of attorney time", never a figure;
  - every AGREEMENT_TYPES / CLAUSE_GLOSSARY / RED_FLAG_DOCTRINE key from the spec
    is present, with the record-vs-distribution ownership/control doctrine and the
    assignment-vs-license "most valuable distinction" framing;
  - every JURISDICTION_DIVERGENCE entry ends with "confirm with local counsel";
  - the BOUNDARIES (OUT_OF_SCOPE) entries route drafting to the owning
    department (split-sheet -> ink-and-air; royalty registration + LOD ->
    ledger-lock; booking memo -> venue-hawk; grants -> fund-phantom).
No service or main.py wiring exists yet at this unit; these tests import the data
module directly.
"""
import ast
import json
import pathlib
import re

import legal_data as ld
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "FOR_YOUR_LAWYER", "CONFIRM_WITH_LOCAL_COUNSEL", "LEX_DOCTRINE",
    "AGREEMENT_TYPES", "AGREEMENT_DOCTRINE", "CLAUSE_GLOSSARY",
    "RED_FLAG_DOCTRINE", "RED_FLAG_DOCTRINE_NOTES", "JURISDICTION_DIVERGENCE",
    "LAWYER_DOCTRINE", "OUT_OF_SCOPE",
)

_SOURCE = pathlib.Path(ld.__file__).read_text(encoding="utf-8")


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(ld, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(ld, name))  # raises TypeError on any leak


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
        json.dumps(getattr(ld, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    money_words = r"(?:dollars?|usd|cad|eur|euros?|gbp|pounds?|cents?|aud|fees?)"
    assert not re.search(rf"\d[\d,\.]*\s*{money_words}", blob), "digit-then-money-word amount found"
    assert not re.search(rf"{money_words}\s*\d", blob), "money-word-then-digit amount found"


def test_lawyer_fee_encoded_as_hours_not_a_figure():
    review = next(p for p in ld.LAWYER_DOCTRINE if p["id"] == "low_cost_routes_exist")
    assert "a few hours of attorney time" in review["principle"]
    # ... and no number sits next to that phrase.
    assert not re.search(r"\d[\d,\.]*\s*hours? of attorney", review["principle"].lower())


# ── AGREEMENT_TYPES coverage + doctrine ────────────────────────────────────────

_EXPECTED_AGREEMENT_KEYS = {
    "band_partnership", "recording_contract", "distribution_deal",
    "publishing_agreement", "management_contract", "booking_agent_agreement",
    "producer_agreement", "sync_license", "three_sixty_deal",
    "work_for_hire_side_artist_session", "beat_license", "letter_of_direction",
    "release_agreement", "minor_parental_consent_guarantee", "nda",
}


def test_all_agreement_types_present_with_full_schema():
    assert set(ld.AGREEMENT_TYPES) == _EXPECTED_AGREEMENT_KEYS
    for key, rec in ld.AGREEMENT_TYPES.items():
        assert rec["key"] == key
        for field in ("display_name", "parties", "purpose", "core_questions",
                      "typical_key_clauses", "owning_department"):
            assert field in rec, f"{key} missing {field}"
        assert isinstance(rec["core_questions"], list) and rec["core_questions"]
        assert isinstance(rec["typical_key_clauses"], list) and rec["typical_key_clauses"]
        assert rec["owning_department"] is None or isinstance(rec["owning_department"], str)


def test_lod_owning_department_is_ledger_lock():
    assert ld.AGREEMENT_TYPES["letter_of_direction"]["owning_department"] == "ledger-lock"


def test_publishing_notes_copub_vs_full():
    text = json.dumps(ld.AGREEMENT_TYPES["publishing_agreement"]).lower()
    assert "co-pub" in text and "full" in text


def test_record_vs_distribution_doctrine_is_ownership_and_control():
    doctrine = ld.AGREEMENT_DOCTRINE["record_deal_vs_distribution_deal"].lower()
    assert "ownership" in doctrine and "control" in doctrine
    assert "distribution" in doctrine


# ── CLAUSE_GLOSSARY coverage ───────────────────────────────────────────────────

_EXPECTED_CLAUSE_TERMS = {
    "assignment_vs_license", "advance", "recoupment_scope",
    "cross_collateralization", "term_and_options", "exclusivity_and_carveouts",
    "reversion", "audit_rights", "discretion_language", "assignment_of_contract",
    "controlled_composition",
}


def test_all_clause_terms_present_with_full_schema():
    assert set(ld.CLAUSE_GLOSSARY) == _EXPECTED_CLAUSE_TERMS
    for term, rec in ld.CLAUSE_GLOSSARY.items():
        assert rec["term"] == term
        for field in ("mechanism", "why_it_matters", "ask_counsel"):
            assert rec.get(field), f"{term} missing {field}"


def test_assignment_vs_license_flagged_most_valuable_distinction():
    assert "most valuable" in ld.CLAUSE_GLOSSARY["assignment_vs_license"]["why_it_matters"].lower()


def test_advance_is_a_loan_against_future_income():
    mech = ld.CLAUSE_GLOSSARY["advance"]["mechanism"].lower()
    assert "loan" in mech and "future income" in mech


def test_controlled_composition_cross_refs_owning_departments():
    text = json.dumps(ld.CLAUSE_GLOSSARY["controlled_composition"]).lower()
    assert "ink-and-air" in text and "ledger-lock" in text


# ── RED_FLAG_DOCTRINE coverage + levers-as-questions ───────────────────────────

_EXPECTED_FLAG_KEYS = {
    "perpetual_master_ownership", "unsupported_360", "commission_stacking",
    "work_for_hire_on_own_artistry", "missing_audit_rights",
    "long_rerecord_restrictions", "automatic_renewal",
    "cross_collateralization_broad", "sign_now_pressure", "conflicted_counsel",
}


def test_all_red_flags_present_with_question_levers():
    assert set(ld.RED_FLAG_DOCTRINE) == _EXPECTED_FLAG_KEYS
    for flag, rec in ld.RED_FLAG_DOCTRINE.items():
        assert rec["flag"] == flag
        assert rec.get("pattern") and rec.get("why_it_matters")
        levers = rec["counsel_levers"]
        assert isinstance(levers, list) and levers
        # Levers are framed as QUESTIONS for counsel, never asserted positions.
        for lever in levers:
            assert lever.rstrip().endswith("?"), f"{flag} lever is not a question: {lever!r}"


def test_perpetual_pattern_names_the_perpetuity_language():
    pat = ld.RED_FLAG_DOCTRINE["perpetual_master_ownership"]["pattern"].lower()
    assert "in perpetuity" in pat and "throughout the universe" in pat


def test_sign_now_pressure_is_itself_a_red_flag_survives_two_week_review():
    rec = json.dumps(ld.RED_FLAG_DOCTRINE["sign_now_pressure"]).lower()
    assert "two-week" in rec or "two week" in rec


def test_red_flag_notes_negotiate_not_always_walk():
    notes = json.dumps(ld.RED_FLAG_DOCTRINE_NOTES).lower()
    assert "negotiate" in notes
    assert "refus" in notes  # refusal to negotiate is its own red flag


# ── JURISDICTION_DIVERGENCE — the counsel string, on every entry ───────────────

_EXPECTED_JURISDICTION_TOPICS = {
    "work_for_hire", "statutory_termination", "moral_rights", "minors",
}


def test_all_jurisdiction_topics_present():
    assert set(ld.JURISDICTION_DIVERGENCE) == _EXPECTED_JURISDICTION_TOPICS


def test_every_jurisdiction_entry_ends_with_confirm_with_local_counsel():
    for topic, rec in ld.JURISDICTION_DIVERGENCE.items():
        note = rec["note"].rstrip()
        assert note.endswith(ld.CONFIRM_WITH_LOCAL_COUNSEL + "."), (
            f"{topic} note does not end with the counsel string: {note!r}"
        )
        assert rec["topic"] == topic
        assert rec.get("mechanism")


def test_work_for_hire_us_only_and_no_canadian_significance():
    mech = ld.JURISDICTION_DIVERGENCE["work_for_hire"]["mechanism"].lower()
    assert "us" in mech and "canad" in mech
    assert "assign" in mech  # belt-and-suspenders fallback pattern


def test_moral_rights_us_visual_art_only_and_uk_not_sound_recordings():
    mech = ld.JURISDICTION_DIVERGENCE["moral_rights"]["mechanism"].lower()
    assert "visual art" in mech
    assert "sound recording" in mech


def test_minors_always_needs_jurisdiction():
    rec = json.dumps(ld.JURISDICTION_DIVERGENCE["minors"]).lower()
    assert "[needs:jurisdiction]" in rec


# ── LAWYER_DOCTRINE + BOUNDARIES ───────────────────────────────────────────────

def test_lawyer_doctrine_covers_independent_counsel_and_no_pressure():
    ids = {p["id"] for p in ld.LAWYER_DOCTRINE}
    assert "independent_counsel_only" in ids
    assert "never_sign_under_pressure" in ids
    assert "read_the_actual_contract" in ids


_EXPECTED_BOUNDARY_ROUTES = {
    "split_sheet": "ink-and-air",
    "royalty_registration": "ledger-lock",
    "lod_drafting": "ledger-lock",
    "booking_deal_memo": "venue-hawk",
    "grant_application": "fund-phantom",
}


def test_boundaries_route_drafting_to_owning_departments():
    for key, dept in _EXPECTED_BOUNDARY_ROUTES.items():
        assert key in ld.OUT_OF_SCOPE, f"missing boundary entry: {key}"
        rec = ld.OUT_OF_SCOPE[key]
        assert rec["owning_department"] == dept, f"{key} routes to wrong department"
        assert rec.get("what") and rec.get("lex_role")


# ── THE ONE RULE ABOVE ALL — no advice / no signable assurance in the corpus ───

def test_corpus_carries_no_signable_assurance_language():
    blob = "\n".join(
        json.dumps(getattr(ld, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    for banned in ("safe to sign", "this contract is fine", "standard to sign",
                   "fine to sign", "ok to sign", "okay to sign"):
        assert banned not in blob, f"assurance language leaked into corpus: {banned!r}"
