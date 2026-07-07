"""
PROOF tests — analytics_data (Data Unit 1, corpus only).

Asserts the structured analytics corpus faithfully encodes
DATA_ANALYTICS_MAP_v1:
  - module-level guarantees: data-only (no def/class/import/call),
    JSON-serializable throughout, entity-wall clean;
  - ZERO currency symbols anywhere — this is a streaming/audience-analytics
    domain, not a money domain, and the corpus never states a dollar figure;
  - METRIC_DEFINITIONS defines stream (30-second threshold, skip is a
    negative algorithmic signal), monthly_listeners (rolling 28-day unique
    window), saves (top engagement signal), followers (fan proxy,
    release-notification opt-in), save_rate (artist-computed, never
    invented), and streams_per_listener_ratio;
  - INTERPRETATION_BANDS frames every band as a NOTE, never a verdict, with
    a "context matters" caveat on the ratio bands, and covers both the
    ratio bands and the skip-rate bands;
  - SOURCE_BREAKDOWN covers profile/catalog, algorithmic, editorial, and
    listener-playlist streams;
  - DIAGNOSIS_PAIRS covers the four named patterns, distinguishing the
    retention problem from the discovery problem;
  - QUALITY_VS_VANITY distinguishes vanity metrics from quality metrics and
    states a small engaged audience beats a large passive one;
  - STAKEHOLDER_FRAMING covers venues/agents and labels/A&R;
  - INTEGRITY carries the two hard rules, especially never_fabricate_numbers
    (the single most important doctrine in this corpus);
  - BOUNDARIES routes execution to kai/aria/mo/miles by name, never claiming
    their work;
  - every doctrine dict's entries satisfy entry["key"] == dict_key.
No service or main.py wiring exists yet at this unit; these tests import the
data module directly.
"""
import ast
import json
import pathlib
import re

import analytics_data as ad
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "DATA_DOCTRINE", "METRIC_DEFINITIONS", "INTERPRETATION_BANDS",
    "SOURCE_BREAKDOWN", "DIAGNOSIS_PAIRS", "QUALITY_VS_VANITY",
    "STAKEHOLDER_FRAMING", "INTEGRITY", "BOUNDARIES",
)

_SOURCE = pathlib.Path(ad.__file__).read_text(encoding="utf-8")

_KEYED_BLOCKS = (
    "METRIC_DEFINITIONS", "INTERPRETATION_BANDS", "SOURCE_BREAKDOWN",
    "DIAGNOSIS_PAIRS", "QUALITY_VS_VANITY", "STAKEHOLDER_FRAMING",
    "INTEGRITY", "BOUNDARIES",
)


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(ad, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(ad, name))  # raises TypeError on any leak


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


# ── ZERO currency symbols anywhere ─────────────────────────────────────────────

def test_no_currency_symbols_anywhere_in_source():
    for symbol in ("$", "£", "€", "¥", "₹", "¢", "₩"):
        assert symbol not in _SOURCE, f"currency symbol {symbol!r} leaked into the corpus"


def test_no_currency_amounts_in_serialized_corpus():
    blob = "\n".join(
        json.dumps(getattr(ad, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    for symbol in ("$", "£", "€", "¥", "₹", "¢", "₩"):
        assert symbol not in blob
    money_words = r"(?:dollars?|usd|cad|eur|euros?|gbp|pounds?|cents?|aud|fees?|revenue)"
    assert not re.search(rf"\d[\d,\.]*\s*{money_words}", blob), "digit-then-money-word amount found"
    assert not re.search(rf"{money_words}\s*\d", blob), "money-word-then-digit amount found"


def test_data_doctrine_bans_dollar_figures():
    text = json.dumps(ad.DATA_DOCTRINE).lower()
    assert "dollar figure" in text or "fee amount" in text or "revenue amount" in text


# ── every doctrine dict's entries satisfy entry["key"] == dict_key ────────────

def test_every_keyed_block_entry_key_matches_dict_key():
    for block_name in _KEYED_BLOCKS:
        block = getattr(ad, block_name)
        assert isinstance(block, dict) and block, f"{block_name} must be a non-empty dict"
        for key, rec in block.items():
            assert isinstance(rec, dict), f"{block_name}[{key}] must be a dict"
            assert rec.get("key") == key, f"{block_name}[{key}] key mismatch: {rec.get('key')!r}"
            assert rec.get("description"), f"{block_name}[{key}] missing description"


# ── METRIC_DEFINITIONS coverage ────────────────────────────────────────────────

_EXPECTED_METRIC_KEYS = {
    "stream", "monthly_listeners", "saves", "followers", "save_rate",
    "streams_per_listener_ratio",
}


def test_all_metric_definition_keys_present():
    assert set(ad.METRIC_DEFINITIONS) == _EXPECTED_METRIC_KEYS


def test_stream_definition_has_30_second_threshold_and_skip_signal():
    text = ad.METRIC_DEFINITIONS["stream"]["description"].lower()
    assert "30" in text and "second" in text
    assert "skip" in text
    assert "negative algorithmic signal" in text


def test_monthly_listeners_is_rolling_28_day_unique_window():
    text = ad.METRIC_DEFINITIONS["monthly_listeners"]["description"].lower()
    assert "28-day" in text
    assert "unique" in text
    assert "rolling" in text


def test_saves_is_top_engagement_signal():
    text = ad.METRIC_DEFINITIONS["saves"]["description"].lower()
    assert "library" in text or "playlist" in text
    assert "top engagement signal" in text


def test_followers_is_fan_proxy_with_release_notification():
    text = ad.METRIC_DEFINITIONS["followers"]["description"].lower()
    assert "fan" in text
    assert "notified" in text and "release" in text


def test_save_rate_is_artist_computed_never_invented():
    rec = ad.METRIC_DEFINITIONS["save_rate"]
    text = rec["description"].lower()
    assert "artist-computed" in text
    assert "never invents" in text or "never invented" in text
    assert rec["formula"] == "saves / streams"


def test_streams_per_listener_ratio_formula():
    rec = ad.METRIC_DEFINITIONS["streams_per_listener_ratio"]
    assert rec["formula"] == "streams / monthly_listeners"


# ── INTERPRETATION_BANDS coverage ──────────────────────────────────────────────

_EXPECTED_BAND_KEYS = {
    "ratio_passive_reach", "ratio_moderate_engagement",
    "ratio_strong_fanbase_activity", "skip_rate_high", "skip_rate_normal",
    "skip_rate_strong",
}


def test_all_interpretation_band_keys_present():
    assert set(ad.INTERPRETATION_BANDS) == _EXPECTED_BAND_KEYS


def test_every_band_is_a_note_not_a_verdict():
    for key, rec in ad.INTERPRETATION_BANDS.items():
        text = rec["description"].lower()
        assert "note" in text and "verdict" in text, f"{key} missing note/verdict framing"


def test_ratio_bands_carry_context_matters_caveat():
    for key in ("ratio_passive_reach", "ratio_moderate_engagement",
                "ratio_strong_fanbase_activity"):
        text = ad.INTERPRETATION_BANDS[key]["description"].lower()
        assert "context matters" in text, f"{key} missing context-matters caveat"


def test_ratio_band_labels_and_meanings():
    assert ad.INTERPRETATION_BANDS["ratio_passive_reach"]["range_label"] == "1:1-1:2"
    assert "passive reach" in ad.INTERPRETATION_BANDS["ratio_passive_reach"]["description"].lower()
    assert ad.INTERPRETATION_BANDS["ratio_moderate_engagement"]["range_label"] == "1:3-1:5"
    assert "moderate engagement" in ad.INTERPRETATION_BANDS["ratio_moderate_engagement"]["description"].lower()
    assert ad.INTERPRETATION_BANDS["ratio_strong_fanbase_activity"]["range_label"] == "1:6+"
    assert "strong fanbase activity" in ad.INTERPRETATION_BANDS["ratio_strong_fanbase_activity"]["description"].lower()


def test_skip_rate_high_flags_intro_and_wrong_audience_playlists():
    text = ad.INTERPRETATION_BANDS["skip_rate_high"]["description"].lower()
    assert "40%" in text
    assert "not hooking listeners" in text
    assert "intro" in text and "too long" in text
    assert "wrong-audience playlists" in text


def test_skip_rate_normal_is_25_to_40_percent():
    rec = ad.INTERPRETATION_BANDS["skip_rate_normal"]
    assert rec["range_label"] == "25%-40%"
    assert "normal" in rec["description"].lower()


def test_skip_rate_strong_prioritizes_for_promotion():
    text = ad.INTERPRETATION_BANDS["skip_rate_strong"]["description"].lower()
    assert "under 25%" in text
    assert "strong" in text
    assert "prioritize for promotion" in text


# ── SOURCE_BREAKDOWN coverage ──────────────────────────────────────────────────

_EXPECTED_SOURCE_KEYS = {
    "profile_catalog_streams", "algorithmic", "editorial", "listener_playlists",
}


def test_all_source_breakdown_keys_present():
    assert set(ad.SOURCE_BREAKDOWN) == _EXPECTED_SOURCE_KEYS


def test_profile_catalog_streams_is_strongest_signal_at_30_percent():
    text = ad.SOURCE_BREAKDOWN["profile_catalog_streams"]["description"].lower()
    assert "30%" in text
    assert "strongest signal" in text
    assert "seeking the artist out directly" in text


def test_algorithmic_is_growth_but_volatile():
    text = ad.SOURCE_BREAKDOWN["algorithmic"]["description"].lower()
    assert "growth" in text
    assert "volatile" in text


def test_editorial_is_exposure_not_controlled_by_artist():
    text = ad.SOURCE_BREAKDOWN["editorial"]["description"].lower()
    assert "exposure" in text
    assert "does not control" in text


def test_listener_playlists_correlates_with_saves():
    text = ad.SOURCE_BREAKDOWN["listener_playlists"]["description"].lower()
    assert "organic" in text
    assert "correlates" in text and "saves" in text


# ── DIAGNOSIS_PAIRS coverage ───────────────────────────────────────────────────

_EXPECTED_DIAGNOSIS_KEYS = {
    "high_streams_low_saves", "high_saves_low_streams",
    "playlist_spike_then_ratio_improves", "followers_stay_listeners_fall",
}


def test_all_diagnosis_pair_keys_present():
    assert set(ad.DIAGNOSIS_PAIRS) == _EXPECTED_DIAGNOSIS_KEYS


def test_high_streams_low_saves_is_retention_problem():
    text = ad.DIAGNOSIS_PAIRS["high_streams_low_saves"]["description"].lower()
    assert "retention problem" in text


def test_high_saves_low_streams_is_discovery_problem_and_different_fix():
    text = ad.DIAGNOSIS_PAIRS["high_saves_low_streams"]["description"].lower()
    assert "discovery problem" in text
    assert "different" in text


def test_playlist_spike_then_ratio_improves_is_exposure_first_and_normal():
    text = ad.DIAGNOSIS_PAIRS["playlist_spike_then_ratio_improves"]["description"].lower()
    assert "exposure-first" in text
    assert "normal for small artists" in text
    assert "ratio" in text and "improves" in text


def test_followers_stay_listeners_fall_describes_persistence():
    text = ad.DIAGNOSIS_PAIRS["followers_stay_listeners_fall"]["description"].lower()
    assert "followers" in text
    assert "monthly listeners" in text


# ── QUALITY_VS_VANITY coverage ─────────────────────────────────────────────────

def test_vanity_metrics_lists_total_streams_and_raw_follower_counts():
    rec = ad.QUALITY_VS_VANITY["vanity_metrics"]
    assert set(rec["metrics"]) == {"total_streams", "raw_follower_counts"}


def test_quality_metrics_lists_saves_follows_listen_through_ratio():
    rec = ad.QUALITY_VS_VANITY["quality_metrics"]
    assert set(rec["metrics"]) == {
        "saves", "follows", "listen_through", "follower_to_listener_ratio",
    }


def test_small_engaged_audience_beats_large_passive_one():
    vanity_text = ad.QUALITY_VS_VANITY["vanity_metrics"]["description"].lower()
    quality_text = ad.QUALITY_VS_VANITY["quality_metrics"]["description"].lower()
    assert "small engaged audience beats a large passive one" in vanity_text
    assert "small engaged audience beats a large passive one" in quality_text


# ── STAKEHOLDER_FRAMING coverage ───────────────────────────────────────────────

def test_venues_and_agents_want_city_listeners_and_draw_evidence():
    rec = ad.STAKEHOLDER_FRAMING["venues_and_agents"]
    assert "listeners_in_their_city" in rec["wants"]
    assert "draw_evidence" in rec["wants"]


def test_labels_and_ar_want_growth_trend_save_rate_source_mix_follower_ratio():
    rec = ad.STAKEHOLDER_FRAMING["labels_and_ar"]
    for want in ("growth_trend", "save_rate", "source_mix", "follower_ratio"):
        assert want in rec["wants"], f"labels_and_ar missing want: {want!r}"


# ── INTEGRITY coverage (the hard rule) ─────────────────────────────────────────

def test_integrity_has_both_hard_rules():
    assert set(ad.INTEGRITY) == {
        "never_loop_or_incentivize_streams", "never_fabricate_numbers",
    }


def test_never_loop_or_incentivize_streams_flags_artificial_and_filtered():
    text = ad.INTEGRITY["never_loop_or_incentivize_streams"]["description"].lower()
    assert "artificial" in text
    assert "filter" in text or "penaliz" in text


def test_never_fabricate_numbers_is_nonempty_and_uses_artist_supplied_and_needs_tags():
    rec = ad.INTEGRITY["never_fabricate_numbers"]
    text = rec["description"]
    assert text and text.strip()
    assert "[ARTIST-SUPPLIED:metrics]" in text
    assert "[NEEDS:" in text
    assert "single most important doctrine" in text.lower()


# ── BOUNDARIES coverage — routes to kai/aria/mo/miles by name ─────────────────

def test_acting_on_insights_boundary_exists_with_owning_departments():
    rec = ad.BOUNDARIES["acting_on_insights"]
    assert set(rec["owning_departments"]) == {
        "grid-prophet", "fan-builder", "mobile-monetize", "tour-commander",
    }


def test_boundaries_name_all_four_owning_agents():
    text = ad.BOUNDARIES["acting_on_insights"]["description"].lower()
    for agent in ("kai", "aria", "mo", "miles"):
        assert agent in text, f"BOUNDARIES missing agent name: {agent!r}"
    assert "grid-prophet" in text
    assert "fan-builder" in text
    assert "mobile-monetize" in text
    assert "tour-commander" in text


def test_boundaries_never_claims_execution_work():
    text = ad.BOUNDARIES["acting_on_insights"]["description"].lower()
    assert "never claims their execution work" in text
