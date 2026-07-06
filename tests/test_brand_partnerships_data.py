"""
PROOF tests — brand_partnerships_data (Nia Unit 1, corpus only).

Asserts the brand-partnerships doctrine corpus faithfully encodes the map: the
structural DEAL_TERMS anatomy (deliverables / compensation / usage_rights /
exclusivity / approval_workflow / disclosure / termination_morals, each a
stable-id record), the structural BRAND_CATEGORIES surface (with the gated
categories — alcohol age-gated, finance regulated — noted), the OUTREACH_DOCTRINE
(personalized, evidence-led, materials cross-referenced to the creative
department, rates never invented), and the section-honesty rules with stable
ids — plus the module-level guarantees: data-only (no def/class/import/call),
JSON-serializable throughout, entity-wall clean, and the Nia-SPECIFIC hard rule
that NO currency amount appears anywhere in source (compensation amounts are
None; a numeric scan enforces it). No service or main.py wiring exists yet;
these tests import the data module directly.
"""
import ast
import json
import pathlib
import re

import brand_partnerships_data as bd
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = ("DEAL_TERMS", "BRAND_CATEGORIES", "OUTREACH_DOCTRINE",
                        "HONESTY_RULES")

_SOURCE = pathlib.Path(bd.__file__).read_text(encoding="utf-8")


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(bd, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(bd, name))  # raises TypeError on any leak


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
    # The whole point of this corpus is that it never quotes a rate. A '$' or any
    # 3+-digit run would signal an invented currency amount. The only digits that
    # may appear are the small duration/window numbers (e.g. 30-90, 48-72).
    assert "$" not in _SOURCE, "no currency symbol may appear in the corpus"
    for run in re.findall(r"\d+", _SOURCE):
        assert len(run) <= 2, f"suspicious numeric run (possible currency amount): {run}"


def test_compensation_amounts_are_none_never_quoted():
    comp = next(r for r in bd.DEAL_TERMS if r["id"] == "compensation")
    assert comp["amounts"] is None
    assert "never" in comp["amounts_note"].lower()
    assert set(comp["models"]) == {"flat", "per_post", "performance_hybrid"}
    assert comp["payment_trigger_and_timeline"]  # must be explicit — present


# ── DEAL_TERMS structural coverage ─────────────────────────────────────────────

def test_deal_terms_ids_complete_and_stable():
    ids = [r["id"] for r in bd.DEAL_TERMS]
    assert ids == ["deliverables", "compensation", "usage_rights", "exclusivity",
                   "approval_workflow", "disclosure", "termination_morals"]


def test_deliverables_demand_exact_counts_not_a_few_posts():
    d = next(r for r in bd.DEAL_TERMS if r["id"] == "deliverables")
    assert set(d["must_be_explicit"]) == {"count", "format", "platform", "date"}
    assert "a few posts" in d["note"].lower()  # the anti-pattern is named
    assert "exact" in d["note"].lower()


def test_usage_and_exclusivity_carry_typical_framing():
    # REQUIRED: the usage-rights baseline and the exclusivity window are framed as
    # a TYPICAL shape, not a hard rule.
    usage = next(r for r in bd.DEAL_TERMS if r["id"] == "usage_rights")
    excl = next(r for r in bd.DEAL_TERMS if r["id"] == "exclusivity")
    assert "typical" in usage["baseline_note"].lower()
    assert "not a rule" in usage["baseline_note"].lower()
    assert "typical" in excl["duration_note"].lower()
    assert set(excl["dimensions"]) == {"category_defined_narrowly", "duration",
                                       "geography", "platform"}


def test_approval_workflow_limits_revisions():
    aw = next(r for r in bd.DEAL_TERMS if r["id"] == "approval_workflow")
    assert aw["revision_rounds_limited"] is True


def test_disclosure_is_convention_not_legal_advice():
    disc = next(r for r in bd.DEAL_TERMS if r["id"] == "disclosure")
    assert "ftc" in disc["mechanism"].lower()
    assert "verify live" in disc["rule"].lower()
    assert "never stated as legal advice" in disc["rule"].lower()


def test_termination_morals_cut_both_directions():
    tm = next(r for r in bd.DEAL_TERMS if r["id"] == "termination_morals")
    assert "both" in tm["note"].lower()


# ── BRAND_CATEGORIES structural surface ────────────────────────────────────────

def test_brand_categories_structural_with_gated_notes():
    by_id = {c["id"]: c for c in bd.BRAND_CATEGORIES}
    for expected in ("fashion_apparel", "beauty", "food_beverage", "alcohol",
                     "tech_audio_gear", "gaming", "lifestyle_wellness",
                     "automotive", "finance_fintech", "travel", "local_business"):
        assert expected in by_id, f"missing category: {expected}"
    assert "age-gated" in by_id["alcohol"]["note"].lower()
    assert "regulated" in by_id["finance_fintech"]["note"].lower()


# ── OUTREACH_DOCTRINE ──────────────────────────────────────────────────────────

def test_outreach_doctrine_materials_cross_ref_and_rates_never_invented():
    od = bd.OUTREACH_DOCTRINE
    assert "creative" in od["materials_ref"].lower()  # EPK -> creative department
    assert "epk" in od["materials_ref"].lower()
    assert "personalized" in od["personalized_pitch_only"].lower()
    assert "invented" in od["rates_never_invented"].lower()
    assert "supplied" in od["rates_never_invented"].lower()


# ── HONESTY_RULES ──────────────────────────────────────────────────────────────

def test_honesty_rules_ids_and_shape():
    ids = [r["id"] for r in bd.HONESTY_RULES]
    assert ids == ["no_market_rates_ever", "deal_evaluation_is_structural",
                   "disclosure_not_legal_advice", "facts_supplied_or_marked"]
    for r in bd.HONESTY_RULES:
        assert r["statement"] and r["allowed"] and r["forbidden"]


def test_deal_evaluation_is_structural_rule_present():
    rule = next(r for r in bd.HONESTY_RULES if r["id"] == "deal_evaluation_is_structural")
    assert "never" in rule["statement"].lower()
    assert "verdict" in rule["statement"].lower()
    assert "good" in rule["forbidden"].lower()
