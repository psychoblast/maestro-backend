"""
PROOF tests — engagement_data (Aria Unit 1, corpus only).

Asserts the structured fan-engagement corpus faithfully encodes
ARIA_ENGAGEMENT_MAP_v1:
  - module-level guarantees: data-only (no def/class/import/call),
    JSON-serializable throughout, entity-wall clean;
  - ZERO currency symbols or amounts anywhere;
  - FAN_FUNNEL carries the four funnel stages (discovery, interest,
    connection, advocacy) and the three fan tiers (casual, true_fan,
    superfan), plus the doctrine that each phase/tier needs a different
    strategy and that superfans — a small percentage of the audience driving
    most word-of-mouth, ticket sales, and merch purchases — deserve
    prioritized attention (equal energy across tiers is the classic mistake);
  - THOUSAND_TRUE_FANS carries the depth-over-scale principle with no fan
    counts or figures;
  - SUPERFAN_IDENTIFICATION carries the behavioral signals and the
    track/recognize + private small-group-access nurture practice;
  - OWNED_CHANNELS distinguishes owned (email/SMS) from rented (social),
    the "subscribers get news first" doctrine, social as top-of-funnel,
    genuine two-way replies, and the in-person merch table doctrine;
  - CADENCE_SPEC carries the weekly and per-release-cycle cadences plus the
    consistency-over-intensity doctrine;
  - WHAT_WASTES_TIME names the four low-leverage patterns;
  - BOUNDARIES routes post scheduling to grid-prophet, fanbase monetization
    to mobile-monetize, and states Aria never fakes/simulates email/SMS
    sending (future integration only).
No service or main.py wiring exists yet at this unit; these tests import the
data module directly.
"""
import ast
import json
import pathlib
import re

import engagement_data as ed
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "ARIA_DOCTRINE", "FAN_FUNNEL", "THOUSAND_TRUE_FANS",
    "SUPERFAN_IDENTIFICATION", "OWNED_CHANNELS", "CADENCE_SPEC",
    "WHAT_WASTES_TIME", "BOUNDARIES",
)

_SOURCE = pathlib.Path(ed.__file__).read_text(encoding="utf-8")


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(ed, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(ed, name))  # raises TypeError on any leak


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
        json.dumps(getattr(ed, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    money_words = r"(?:dollars?|usd|cad|eur|euros?|gbp|pounds?|cents?|aud|fees?)"
    assert not re.search(rf"\d[\d,\.]*\s*{money_words}", blob), "digit-then-money-word amount found"
    assert not re.search(rf"{money_words}\s*\d", blob), "money-word-then-digit amount found"


# ── ARIA_DOCTRINE coverage ──────────────────────────────────────────────────────

_EXPECTED_DOCTRINE_KEYS = {
    "depth_over_scale", "superfans_first", "owned_over_rented",
    "never_simulates_sending",
}


def test_all_doctrine_keys_present():
    assert _EXPECTED_DOCTRINE_KEYS <= set(ed.ARIA_DOCTRINE)
    for key, text in ed.ARIA_DOCTRINE.items():
        assert isinstance(text, str) and text.strip()


def test_doctrine_superfans_first_names_the_classic_mistake():
    text = ed.ARIA_DOCTRINE["superfans_first"].lower()
    assert "small percentage" in text
    assert "classic mistake" in text


def test_doctrine_owned_over_rented_names_inner_circle_and_top_of_funnel():
    text = ed.ARIA_DOCTRINE["owned_over_rented"].lower()
    assert "inner circle" in text
    assert "top-of-funnel" in text


def test_doctrine_never_simulates_sending():
    text = ed.ARIA_DOCTRINE["never_simulates_sending"].lower()
    assert "never" in text
    assert "sent an email" in text or "sending" in text


# ── FAN_FUNNEL coverage + doctrine ─────────────────────────────────────────────

_EXPECTED_FUNNEL_KEYS = {
    "discovery", "interest", "connection", "advocacy",
    "casual", "true_fan", "superfan",
    "tier_and_stage_prioritization_doctrine",
}


def test_all_fan_funnel_keys_present_with_schema():
    assert set(ed.FAN_FUNNEL) == _EXPECTED_FUNNEL_KEYS
    for key, rec in ed.FAN_FUNNEL.items():
        assert rec["key"] == key
        assert rec.get("category") in ("funnel_stage", "fan_tier", "doctrine")
        assert rec.get("description")


def test_four_funnel_stages_categorized_correctly():
    for stage in ("discovery", "interest", "connection", "advocacy"):
        assert ed.FAN_FUNNEL[stage]["category"] == "funnel_stage"


def test_three_fan_tiers_categorized_correctly():
    for tier in ("casual", "true_fan", "superfan"):
        assert ed.FAN_FUNNEL[tier]["category"] == "fan_tier"


def test_superfan_prioritization_doctrine_present_and_nonempty():
    doctrine = ed.FAN_FUNNEL["tier_and_stage_prioritization_doctrine"]
    assert doctrine["category"] == "doctrine"
    text = doctrine["description"]
    assert isinstance(text, str) and text.strip()
    lowered = text.lower()
    assert "small percentage" in lowered
    assert "word-of-mouth" in lowered
    assert "ticket sales" in lowered
    assert "merch" in lowered
    assert "equal energy" in lowered
    assert "classic mistake" in lowered


def test_superfan_tier_entry_names_outsized_impact():
    text = ed.FAN_FUNNEL["superfan"]["description"].lower()
    assert "small percentage" in text
    assert "word-of-mouth" in text


# ── THOUSAND_TRUE_FANS coverage — no fan-count numbers ─────────────────────────

def test_thousand_true_fans_has_at_least_one_principle_entry():
    assert len(ed.THOUSAND_TRUE_FANS) >= 1
    for key, rec in ed.THOUSAND_TRUE_FANS.items():
        assert rec["key"] == key
        assert rec.get("category") == "principle"
        assert rec.get("description")


def test_depth_over_scale_principle_present():
    text = ed.THOUSAND_TRUE_FANS["depth_over_scale_principle"]["description"].lower()
    assert "depth" in text
    assert "scale" in text


def test_thousand_true_fans_contains_no_digits():
    # ensure_ascii=False so em-dashes don't serialize to — (a false-positive digit).
    blob = json.dumps(ed.THOUSAND_TRUE_FANS, ensure_ascii=False)
    assert not re.search(r"\d", blob), "THOUSAND_TRUE_FANS must contain no numbers/figures"


# ── SUPERFAN_IDENTIFICATION coverage ────────────────────────────────────────────

_EXPECTED_SUPERFAN_SIGNAL_KEYS = {
    "comments_on_every_post", "shares_unprompted", "buys_repeatedly",
    "creates_fan_content", "saves_and_repeat_listens_within_48_hours",
}

_EXPECTED_SUPERFAN_PRACTICE_KEYS = {
    "track_and_recognize_practice", "private_small_group_access_nurture_pattern",
}


def test_all_superfan_identification_keys_present_with_schema():
    assert set(ed.SUPERFAN_IDENTIFICATION) == (
        _EXPECTED_SUPERFAN_SIGNAL_KEYS | _EXPECTED_SUPERFAN_PRACTICE_KEYS
    )
    for key, rec in ed.SUPERFAN_IDENTIFICATION.items():
        assert rec["key"] == key
        assert rec.get("category") in ("behavioral_signal", "practice")
        assert rec.get("description")


def test_superfan_behavioral_signals_categorized_correctly():
    for key in _EXPECTED_SUPERFAN_SIGNAL_KEYS:
        assert ed.SUPERFAN_IDENTIFICATION[key]["category"] == "behavioral_signal"


def test_saves_and_repeat_listens_signal_mentions_48_hours():
    text = ed.SUPERFAN_IDENTIFICATION["saves_and_repeat_listens_within_48_hours"]["description"].lower()
    assert "48 hours" in text


def test_practice_entries_cover_tracking_and_private_access():
    track = ed.SUPERFAN_IDENTIFICATION["track_and_recognize_practice"]["description"].lower()
    assert "track" in track and "recognize" in track
    nurture = ed.SUPERFAN_IDENTIFICATION["private_small_group_access_nurture_pattern"]["description"].lower()
    assert "early listens" in nurture
    assert "vote" in nurture
    assert "merch" in nurture


# ── OWNED_CHANNELS coverage ──────────────────────────────────────────────────────

_EXPECTED_OWNED_CHANNEL_KEYS = {
    "owned_channels_email_sms", "rented_channels_social_media",
    "subscribers_get_news_first_doctrine", "social_as_top_of_funnel_doctrine",
    "genuine_two_way_replies_doctrine", "in_person_merch_table_doctrine",
}


def test_all_owned_channel_keys_present_with_schema():
    assert set(ed.OWNED_CHANNELS) == _EXPECTED_OWNED_CHANNEL_KEYS
    for key, rec in ed.OWNED_CHANNELS.items():
        assert rec["key"] == key
        assert rec.get("category") in ("owned", "rented", "doctrine")
        assert rec.get("description")


def test_owned_vs_rented_channels_distinguished():
    owned = ed.OWNED_CHANNELS["owned_channels_email_sms"]
    rented = ed.OWNED_CHANNELS["rented_channels_social_media"]
    assert owned["category"] == "owned"
    assert rented["category"] == "rented"
    assert "controls" in owned["description"].lower()
    assert "algorithm" in rented["description"].lower()


def test_subscribers_get_news_first_doctrine_states_no_reason_to_stay():
    text = ed.OWNED_CHANNELS["subscribers_get_news_first_doctrine"]["description"].lower()
    assert "first" in text
    assert "no reason" in text


def test_social_framed_as_top_of_funnel_and_owned_as_inner_circle():
    text = ed.OWNED_CHANNELS["social_as_top_of_funnel_doctrine"]["description"].lower()
    assert "top-of-funnel" in text
    assert "inner circle" in text


def test_two_way_replies_and_merch_table_doctrines_present():
    replies = ed.OWNED_CHANNELS["genuine_two_way_replies_doctrine"]["description"].lower()
    assert "real" in replies and "individual" in replies
    merch = ed.OWNED_CHANNELS["in_person_merch_table_doctrine"]["description"].lower()
    assert "merch table" in merch
    assert "online effort" in merch


# ── CADENCE_SPEC coverage ────────────────────────────────────────────────────────

_EXPECTED_CADENCE_KEYS = {
    "weekly_cadence", "per_release_cycle_cadence",
    "consistency_over_intensity_doctrine",
}


def test_all_cadence_keys_present_with_schema():
    assert set(ed.CADENCE_SPEC) == _EXPECTED_CADENCE_KEYS
    for key, rec in ed.CADENCE_SPEC.items():
        assert rec["key"] == key
        assert rec.get("cadence_type") in ("weekly", "per_release_cycle", "doctrine")
        assert isinstance(rec.get("tasks"), list)
        assert rec.get("description")


def test_weekly_cadence_tasks():
    tasks = " ".join(ed.CADENCE_SPEC["weekly_cadence"]["tasks"]).lower()
    assert "comments" in tasks
    assert "superfans" in tasks
    assert "reshare" in tasks


def test_per_release_cycle_cadence_tasks():
    tasks = " ".join(ed.CADENCE_SPEC["per_release_cycle_cadence"]["tasks"]).lower()
    assert "early-access" in tasks
    assert "poll" in tasks or "vote" in tasks
    assert "behind-the-work" in tasks


def test_consistency_over_intensity_doctrine():
    text = ed.CADENCE_SPEC["consistency_over_intensity_doctrine"]["description"].lower()
    assert "consisten" in text
    assert "silence" in text


# ── WHAT_WASTES_TIME coverage ────────────────────────────────────────────────────

_EXPECTED_WASTES_TIME_KEYS = {
    "replying_to_everything_at_scale", "unplanned_livestreams",
    "chasing_vanity_metrics", "responding_to_trolls",
}


def test_all_wastes_time_keys_present_with_schema():
    assert set(ed.WHAT_WASTES_TIME) == _EXPECTED_WASTES_TIME_KEYS
    for key, rec in ed.WHAT_WASTES_TIME.items():
        assert rec["key"] == key
        assert rec.get("description")


def test_replying_at_scale_contrasted_with_focused_superfan_engagement():
    text = ed.WHAT_WASTES_TIME["replying_to_everything_at_scale"]["description"].lower()
    assert "superfan" in text


# ── BOUNDARIES coverage ──────────────────────────────────────────────────────────

_EXPECTED_BOUNDARY_ROUTES = {
    "post_scheduling_and_execution": "grid-prophet",
    "monetizing_the_fanbase": "mobile-monetize",
}


def test_all_boundary_keys_present_with_schema():
    assert set(ed.BOUNDARIES) == {
        "post_scheduling_and_execution", "monetizing_the_fanbase",
        "email_sms_sending_infrastructure",
    }
    for key, rec in ed.BOUNDARIES.items():
        assert rec["key"] == key
        assert rec.get("what")
        assert "aria_role" in rec and rec["aria_role"]
        assert "owning_department" in rec


def test_boundaries_route_to_owning_departments_by_name():
    for key, dept in _EXPECTED_BOUNDARY_ROUTES.items():
        rec = ed.BOUNDARIES[key]
        assert rec["owning_department"] == dept, f"{key} routes to wrong department"


def test_email_sms_sending_is_future_integration_never_faked():
    rec = ed.BOUNDARIES["email_sms_sending_infrastructure"]
    assert rec["owning_department"] is None
    text = rec["aria_role"].lower()
    assert "never fake" in text or "never" in text and "fake" in text
    assert "simulate" in text
    assert "future integration" in text


# ── key-consistency sweep across every block ────────────────────────────────────

_ALL_DICT_OF_DICT_BLOCKS = (
    ed.FAN_FUNNEL, ed.THOUSAND_TRUE_FANS, ed.SUPERFAN_IDENTIFICATION,
    ed.OWNED_CHANNELS, ed.CADENCE_SPEC, ed.WHAT_WASTES_TIME, ed.BOUNDARIES,
)


def test_every_entry_key_matches_its_dict_key_across_all_blocks():
    for block in _ALL_DICT_OF_DICT_BLOCKS:
        for k, v in block.items():
            assert v["key"] == k, f"entry key mismatch: dict key {k!r} vs entry key {v.get('key')!r}"
