"""
PROOF tests — publicity_data (Zara Unit 1, corpus only).

Asserts the publicity / press doctrine corpus faithfully encodes the map: the
PITCH_MECHANISM_TYPES (standard / embargo / exclusive, with the selection doctrine
and the never-conflate rule), the EMBARGO_DOCTRINE hard rules (explicit agreement
first, zoned lift always, owned-channels negate, moving-the-date damages), the
LEAD_TIME_DOCTRINE (ranges as verify-live notes + a structured campaign_timeline
ordered by lead), the LIST_AND_PERSONALIZATION_DOCTRINE, the PITCH_PACKAGE_SPEC
(components + press-release referenced from the creative department, follow-up
discipline), the INTEGRITY_DOCTRINE, the OUT_OF_SCOPE boundaries (creative-director
/ puppet-master / airwave / brand-connect), and the section-honesty rules — plus
the module-level guarantees: data-only (no def/class/import/call), JSON-serializable
throughout, entity-wall clean, ZERO currency amounts, and NO fabricated outlet /
journalist / contact markers anywhere in source. No service or main.py wiring
exists yet; these tests import the data module directly.
"""
import ast
import json
import pathlib
import re

import publicity_data as pd
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = ("PITCH_MECHANISM_TYPES", "EMBARGO_DOCTRINE",
                        "LEAD_TIME_DOCTRINE", "LIST_AND_PERSONALIZATION_DOCTRINE",
                        "PITCH_PACKAGE_SPEC", "INTEGRITY_DOCTRINE", "OUT_OF_SCOPE",
                        "HONESTY_RULES")

_SOURCE = pathlib.Path(pd.__file__).read_text(encoding="utf-8")
_DATA_TEXT = json.dumps([getattr(pd, n) for n in _TOP_LEVEL_CONSTANTS],
                        ensure_ascii=False)


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(pd, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(pd, name))


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


def test_no_currency_amounts_anywhere():
    assert "$" not in _SOURCE, "no currency symbol may appear in the corpus"
    for run in re.findall(r"\d+", _DATA_TEXT):
        assert len(run) <= 2, f"suspicious numeric run (possible currency amount): {run}"


def test_no_fabricated_outlet_or_contact_markers():
    # Media targets are NEVER encoded — no emails, URLs, or handle markers anywhere.
    low = _SOURCE.lower()
    for marker in ("@", "http", ".com", ".example", "www."):
        assert marker not in low, f"possible fabricated media contact marker: {marker!r}"


# ── PITCH_MECHANISM_TYPES ──────────────────────────────────────────────────────

def test_pitch_mechanism_types_three_distinct_and_not_interchangeable():
    pmt = pd.PITCH_MECHANISM_TYPES
    for k in ("standard", "embargo", "exclusive"):
        assert k in pmt and pmt[k]["note"], f"missing mechanism: {k}"
    assert "anytime" in pmt["standard"]["note"].lower()
    assert "withheld" in pmt["embargo"]["note"].lower()
    assert "one outlet" in pmt["exclusive"]["note"].lower()
    sd = pmt["selection_doctrine"]
    assert "not" in sd["not_interchangeable"].lower()
    assert "conflate" in sd["not_interchangeable"].lower()
    assert "exclusive" in sd["max_impressions"].lower()  # max impressions -> NOT exclusive


# ── EMBARGO_DOCTRINE ───────────────────────────────────────────────────────────

def test_embargo_doctrine_hard_rules():
    ed = pd.EMBARGO_DOCTRINE
    assert "before" in ed["explicit_agreement_first"].lower()
    assert "time zone" in ed["state_timezone_always"].lower()
    assert "negates" in ed["owned_channels_negate"].lower()
    assert "not bound" in ed["moving_the_date_damages"].lower()
    assert "newsworthy" in ed["reserve_for_newsworthy"].lower()


# ── LEAD_TIME_DOCTRINE ─────────────────────────────────────────────────────────

def test_lead_time_ranges_are_notes_and_sustained():
    lt = pd.LEAD_TIME_DOCTRINE
    assert "varies by outlet" in lt["varies_note"].lower()
    assert "sustained" in lt["sustained_not_release_week_only"].lower()
    assert "never release-week-only" in lt["sustained_not_release_week_only"].lower()


def test_campaign_timeline_ordered_by_lead_and_covers_key_slots():
    tl = pd.LEAD_TIME_DOCTRINE["campaign_timeline"]
    weeks = [s["weeks_before_release"] for s in tl]
    assert weeks == sorted(weeks, reverse=True), f"timeline not lead-ordered: {weeks}"
    slots = {s["slot"] for s in tl}
    for expected in ("lead_single", "press_kit_final", "album_announcement",
                     "full_album_stream_premiere", "features_and_reviews_land"):
        assert expected in slots, f"missing timeline slot: {expected}"
    # lead single leads the album announcement; premiere is ~1 week before release.
    by_slot = {s["slot"]: s for s in tl}
    assert by_slot["lead_single"]["weeks_before_release"] > by_slot["album_announcement"]["weeks_before_release"]
    assert by_slot["full_album_stream_premiere"]["weeks_before_release"] == 1
    assert by_slot["features_and_reviews_land"]["weeks_before_release"] == 0


# ── LIST_AND_PERSONALIZATION_DOCTRINE ──────────────────────────────────────────

def test_personalization_doctrine():
    lp = pd.LIST_AND_PERSONALIZATION_DOCTRINE
    assert "personaliz" in lp["personalize_or_rejected"].lower()
    assert "now" in lp["check_current_beat"].lower()
    assert "focused" in lp["focused_beats_generic"].lower()


# ── PITCH_PACKAGE_SPEC ─────────────────────────────────────────────────────────

def test_pitch_package_components_and_press_release_ref():
    ps = pd.PITCH_PACKAGE_SPEC
    for c in ("final_audio_private_link", "artwork", "photos", "bio", "credits",
              "story_angle", "release_date"):
        assert c in ps["components"], f"missing package component: {c}"
    assert "build_copy_scaffold" in ps["press_release_ref"]
    assert "never drafted" in ps["press_release_ref"].lower()
    assert "one follow-up" in ps["follow_up_doctrine"].lower()


# ── INTEGRITY_DOCTRINE ─────────────────────────────────────────────────────────

def test_integrity_earned_never_paid():
    idoc = pd.INTEGRITY_DOCTRINE
    assert "never paid" in idoc["earned_never_paid"].lower()
    assert "red flag" in idoc["earned_never_paid"].lower()
    assert "documented" in idoc["broken_embargo"].lower()


# ── OUT_OF_SCOPE boundaries ────────────────────────────────────────────────────

def test_boundaries_present_and_route_to_right_owners():
    oos = pd.OUT_OF_SCOPE
    assert oos["press_release_drafting"]["owner"] == "creative-director"
    assert oos["press_release_drafting"]["tool"] == "build_copy_scaffold"
    assert oos["curator_outreach"]["owner"] == "puppet-master"
    assert oos["radio_dsp_promotion"]["owner"] == "airwave"
    assert oos["brand_deals"]["owner"] == "brand-connect"
    for entry in oos.values():
        assert entry["reason"]


# ── HONESTY_RULES ──────────────────────────────────────────────────────────────

def test_honesty_rules_ids_and_shape():
    ids = [r["id"] for r in pd.HONESTY_RULES]
    assert ids == ["never_fabricate_media_targets", "drafting_belongs_to_creative",
                   "embargo_needs_zoned_lift", "earned_media_never_paid"]
    for r in pd.HONESTY_RULES:
        assert r["statement"] and r["allowed"] and r["forbidden"]


def test_never_fabricate_media_targets_rule_present():
    rule = next(r for r in pd.HONESTY_RULES if r["id"] == "never_fabricate_media_targets")
    assert "never" in rule["statement"].lower()
    assert "artist-supplied" in rule["statement"].lower()
    assert "outlet name" in rule["forbidden"].lower()
