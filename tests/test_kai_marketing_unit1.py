"""
PROOF tests — digital_marketing_data (Kai Unit 1, corpus only).

Asserts the structured digital-marketing corpus faithfully encodes
KAI_MARKETING_MAP_v1:
  - module-level guarantees: data-only (no def/class/import/call),
    JSON-serializable throughout, entity-wall clean;
  - ZERO currency symbols anywhere in the source, AND a dedicated scan of
    BUDGET_MECHANICS specifically for dollar-figure-shaped patterns;
  - CHANNEL_SEQUENCE's exact ordering (streaming-optimization -> organic ->
    email -> paid-last) is present and named in that order;
  - ORGANIC_PROOF_FIRST's spark-ad / 2-second-hook / prove-before-spend
    doctrine is present;
  - PLATFORM_SELECTION's four channel entries are present with
    objective-based framing and zero prices;
  - BUDGET_MECHANICS's kill-fast / never-all-in / start-small doctrine is
    present;
  - MEASUREMENT's save-rate / follower-add-rate / cost-per-engaged-listener
    naming is present, plus the streams-without-saves fake-growth warning;
  - FIRST_72_HOURS's pre-save + coordinated-landing doctrine is present;
  - INTEGRITY's never-buy-streams-or-followers rule and the
    paid-promotion-is-not-payola distinction (with the signal-blaster
    cross-reference) are present;
  - BOUNDARIES correctly keeps post-scheduling as Kai's own domain while
    routing press to signal-blaster, playlist/curator pitching to
    puppet-master AND airwave, and fan-relationship depth to fan-builder.
No service or main.py wiring exists yet at this unit; these tests import the
data module directly.
"""
import ast
import json
import pathlib
import re

import digital_marketing_data as dmd
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "KAI_DOCTRINE", "CHANNEL_SEQUENCE", "ORGANIC_PROOF_FIRST",
    "PLATFORM_SELECTION", "BUDGET_MECHANICS", "MEASUREMENT",
    "FIRST_72_HOURS", "INTEGRITY", "BOUNDARIES",
)

_SOURCE = pathlib.Path(dmd.__file__).read_text(encoding="utf-8")

# Every block whose entries carry a "key" field that must match the dict key.
_KEYED_BLOCKS = (
    "CHANNEL_SEQUENCE", "ORGANIC_PROOF_FIRST", "PLATFORM_SELECTION",
    "BUDGET_MECHANICS", "MEASUREMENT", "FIRST_72_HOURS", "INTEGRITY",
    "BOUNDARIES",
)


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(dmd, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(dmd, name))  # raises TypeError on any leak


def test_module_is_data_only_no_def_class_or_import_or_call():
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


def test_every_keyed_block_entry_key_matches_dict_key():
    for block_name in _KEYED_BLOCKS:
        block = getattr(dmd, block_name)
        for k, v in block.items():
            assert v["key"] == k, f"{block_name}[{k!r}] has mismatched key {v.get('key')!r}"


# ── ZERO currency symbols anywhere, plus a dedicated BUDGET_MECHANICS scan ─────

def test_no_currency_symbols_anywhere_in_source():
    for symbol in ("$", "£", "€", "¥", "₹", "¢", "₩"):
        assert symbol not in _SOURCE, f"currency symbol {symbol!r} leaked into the corpus"


def test_no_currency_amounts_in_serialized_corpus():
    blob = "\n".join(
        json.dumps(getattr(dmd, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    money_words = r"(?:dollars?|usd|cad|eur|euros?|gbp|pounds?|cents?|aud|fees?|figures?|amounts?)"
    assert not re.search(rf"\d[\d,\.]*\s*{money_words}", blob), "digit-then-money-word amount found"
    assert not re.search(rf"{money_words}\s*\d", blob), "money-word-then-digit amount found"


def test_budget_mechanics_has_zero_dollar_figures_or_percentages():
    # Dedicated, stricter scan of BUDGET_MECHANICS specifically: mechanism and
    # practice only, never a figure. No currency symbols, no digit-shaped spend
    # numbers, and no percentage sign anywhere in this block.
    blob = json.dumps(dmd.BUDGET_MECHANICS, ensure_ascii=False)
    for symbol in ("$", "£", "€", "¥", "₹", "¢", "₩", "%"):
        assert symbol not in blob, f"{symbol!r} leaked into BUDGET_MECHANICS"
    assert not re.search(r"\d", blob), "a digit was found in BUDGET_MECHANICS"


def test_budget_mechanics_keys_present():
    expected = {
        "start_small", "test_multiple_creatives_simultaneously", "kill_fast",
        "never_all_in_on_one_ad", "scale_only_what_already_works",
        "geographic_market_mix_stretches_spend",
    }
    assert set(dmd.BUDGET_MECHANICS) == expected


def test_budget_mechanics_start_small_test_kill_never_all_in_doctrine():
    text = json.dumps(dmd.BUDGET_MECHANICS).lower()
    assert "start small" in text
    assert "multiple creative variants simultaneously" in text
    assert "a couple of days" in text
    assert "kill" in text
    assert "never spend the entire available budget on a single ad" in text
    assert "scale only what has already proven it works" in text


# ── CHANNEL_SEQUENCE coverage ───────────────────────────────────────────────────

def test_channel_sequence_order_is_exact():
    order = dmd.CHANNEL_SEQUENCE["sequencing_order"]["order"]
    assert order == [
        "streaming_platform_optimization",
        "organic_short_form_content",
        "email",
        "paid_promotion",
    ]


def test_channel_sequence_names_ads_amplify_dont_substitute():
    text = dmd.CHANNEL_SEQUENCE["paid_promotion_last"]["description"].lower()
    assert "amplify" in text
    assert "not a substitute" in text


def test_channel_sequence_release_cadence_varies_by_artist():
    text = dmd.CHANNEL_SEQUENCE["release_cadence"]["description"].lower()
    assert "six to eight weeks" in text
    assert "varies" in text
    assert "rigid rule" in text


# ── ORGANIC_PROOF_FIRST coverage ────────────────────────────────────────────────

def test_organic_proof_first_keys_present():
    expected = {
        "spark_ad_pattern", "prove_before_spending",
        "native_lo_fi_outperforms_polished", "two_second_hook",
    }
    assert set(dmd.ORGANIC_PROOF_FIRST) == expected


def test_spark_ad_pattern_present():
    text = dmd.ORGANIC_PROOF_FIRST["spark_ad_pattern"]["description"].lower()
    assert "spark" in text
    assert "already getting traction" in text


def test_two_second_hook_present():
    text = dmd.ORGANIC_PROOF_FIRST["two_second_hook"]["description"].lower()
    assert "two seconds" in text or "2 second" in text or "2-second" in text


def test_prove_before_spending_present():
    text = dmd.ORGANIC_PROOF_FIRST["prove_before_spending"]["description"].lower()
    assert "before" in text and "spending" in text


def test_native_lo_fi_outperforms_polished_present():
    text = dmd.ORGANIC_PROOF_FIRST["native_lo_fi_outperforms_polished"]["description"].lower()
    assert "lo-fi" in text
    assert "outperform" in text


# ── PLATFORM_SELECTION coverage ─────────────────────────────────────────────────

_EXPECTED_CHANNEL_KEYS = {
    "short_video_platforms", "meta_instagram_facebook_advertising",
    "video_pre_roll_advertising", "dsp_audio_ads",
}


def test_all_four_channel_entries_present_with_objective_framing():
    channels = {
        k: v for k, v in dmd.PLATFORM_SELECTION.items() if v["category"] == "channel"
    }
    assert set(channels) == _EXPECTED_CHANNEL_KEYS
    for key, rec in channels.items():
        assert isinstance(rec["best_for"], list) and rec["best_for"], f"{key} missing best_for"


def test_no_prices_anywhere_in_platform_selection():
    blob = json.dumps(dmd.PLATFORM_SELECTION, ensure_ascii=False)
    for symbol in ("$", "£", "€", "¥", "₹", "¢", "₩"):
        assert symbol not in blob, f"{symbol!r} leaked into PLATFORM_SELECTION"


def test_video_pre_roll_is_for_music_video_launches():
    rec = dmd.PLATFORM_SELECTION["video_pre_roll_advertising"]
    assert "music_video_launches" in rec["best_for"]


def test_dsp_audio_ads_is_for_free_tier_ad_supported_listeners():
    text = dmd.PLATFORM_SELECTION["dsp_audio_ads"]["description"].lower()
    assert "free-tier" in text or "free tier" in text
    assert "ad-supported" in text or "ad supported" in text


def test_warm_before_cold_and_broad_can_outperform_manual_doctrine():
    assert "warm_before_cold" in dmd.PLATFORM_SELECTION
    assert "broad_automatic_can_outperform_manual" in dmd.PLATFORM_SELECTION
    text = dmd.PLATFORM_SELECTION["broad_automatic_can_outperform_manual"]["description"].lower()
    assert "broad" in text or "automatic" in text
    assert "manual" in text


# ── MEASUREMENT coverage ────────────────────────────────────────────────────────

def test_measurement_names_save_rate_follower_add_rate_cost_per_engaged_listener():
    for key in ("save_rate", "follower_add_rate", "cost_per_engaged_listener"):
        assert key in dmd.MEASUREMENT, f"missing measurement metric: {key}"


def test_measurement_streams_without_saves_is_fake_growth_warning():
    text = dmd.MEASUREMENT["streams_without_saves_is_fake_growth_warning"]["description"].lower()
    assert "fake" in text
    assert "saves" in text


def test_measurement_not_raw_impressions_or_streams_alone():
    text = dmd.MEASUREMENT["not_raw_impressions_or_streams_alone"]["description"].lower()
    assert "impressions" in text
    assert "streams" in text


def test_measurement_correlate_against_campaign_calendar():
    text = dmd.MEASUREMENT["correlate_against_campaign_calendar"]["description"].lower()
    assert "campaign calendar" in text


# ── FIRST_72_HOURS coverage ─────────────────────────────────────────────────────

def test_first_72_hours_pre_save_and_coordinated_landing_present():
    assert "pre_save_campaigns_build_early_signal" in dmd.FIRST_72_HOURS
    assert "coordinate_owned_organic_paid_landing_together" in dmd.FIRST_72_HOURS
    text = dmd.FIRST_72_HOURS["platforms_reward_early_momentum"]["description"].lower()
    assert "48 to 72 hours" in text


def test_first_72_hours_coordination_names_email_organic_paid():
    text = dmd.FIRST_72_HOURS["coordinate_owned_organic_paid_landing_together"]["description"].lower()
    assert "email" in text or "sms" in text
    assert "organic" in text
    assert "paid" in text


# ── INTEGRITY coverage — the hard rule ──────────────────────────────────────────

def test_integrity_keys_present():
    assert set(dmd.INTEGRITY) == {
        "never_buy_streams_or_followers", "paid_promotion_is_not_payola",
    }


def test_never_buy_streams_or_followers_rule_is_absolute():
    text = dmd.INTEGRITY["never_buy_streams_or_followers"]["description"].lower()
    assert "never" in text
    assert "buying streams" in text or "buy streams" in text
    assert "buying followers" in text or "buy followers" in text
    assert "fabricat" in text


def test_paid_promotion_is_not_payola_cross_refs_signal_blaster():
    text = dmd.INTEGRITY["paid_promotion_is_not_payola"]["description"].lower()
    assert "payola" in text
    assert "signal-blaster" in text
    assert "not" in text


def test_kai_doctrine_never_buys_growth_cross_refs_data_oracle():
    text = json.dumps(dmd.KAI_DOCTRINE).lower()
    assert "never" in text and ("buy" in text or "buying" in text)
    assert "data-oracle" in text


# ── BOUNDARIES coverage ─────────────────────────────────────────────────────────

def test_post_scheduling_is_kais_own_domain_not_routed_away():
    rec = dmd.BOUNDARIES["post_scheduling_and_execution_is_kais_own_domain"]
    assert rec["owning_department"] is None
    text = rec["kai_role"].lower()
    assert "kai's own domain" in text or "kai is" in text or "grid-prophet is kai" in text


def test_press_routes_to_signal_blaster():
    rec = dmd.BOUNDARIES["press_and_earned_media"]
    assert rec["owning_department"] == "signal-blaster"


def test_playlist_and_curator_pitching_routes_to_both_puppet_master_and_airwave():
    rec = dmd.BOUNDARIES["playlist_and_curator_pitching"]
    dept = rec["owning_department"]
    assert isinstance(dept, list)
    assert "puppet-master" in dept
    assert "airwave" in dept


def test_fan_relationship_depth_routes_to_fan_builder():
    rec = dmd.BOUNDARIES["fan_relationship_depth_and_nurture"]
    assert rec["owning_department"] == "fan-builder"


def test_boundaries_state_kai_role_for_every_entry():
    for key, rec in dmd.BOUNDARIES.items():
        assert rec.get("what")
        assert rec.get("kai_role")
