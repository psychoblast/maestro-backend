"""
PROOF tests — monetization_data (Mo Unit 1, corpus only).

Asserts the structured revenue-diversification corpus faithfully encodes
MO_MONETIZATION_MAP_v1:
  - module-level guarantees: data-only (no def/class/import/call),
    JSON-serializable throughout, entity-wall clean;
  - ZERO currency symbols anywhere, ZERO digit-adjacent money-word patterns,
    and — because this domain is explicitly about money — ZERO digits at all
    anywhere in the serialized corpus, so no dollar-figure-shaped pattern of
    any kind can exist;
  - REVENUE_STREAM_TAXONOMY carries all 10 streams with mechanism /
    prerequisites / payment_pattern / owning_department;
  - DIVERSIFICATION carries the three-to-five-stream doctrine and the three
    named compounding relationships (live->merch, streaming->sync,
    teaching->session-credibility);
  - SEQUENCING correctly splits audience-independent (teaching/session work)
    from audience-dependent (merch/subscriptions/streaming) streams;
  - ADMIN names the sloppy-metadata-loses-money mechanism;
  - INTEGRITY locks the never-a-dollar-figure rule;
  - BOUNDARIES routes execution to fund-phantom / brand-connect /
    ledger-lock / ink-and-air / tour-commander by name.
No service or main.py wiring exists yet at this unit; these tests import the
data module directly.
"""
import ast
import json
import pathlib
import re

import monetization_data as md
from entity_wall_terms import assert_no_forbidden_terms

_TOP_LEVEL_CONSTANTS = (
    "MO_DOCTRINE", "REVENUE_STREAM_TAXONOMY", "DIVERSIFICATION", "SEQUENCING",
    "ADMIN", "INTEGRITY", "BOUNDARIES",
)

_SOURCE = pathlib.Path(md.__file__).read_text(encoding="utf-8")

# Every block whose entries carry a "key" field that must match the dict key.
_KEYED_BLOCKS = (
    "REVENUE_STREAM_TAXONOMY", "DIVERSIFICATION", "SEQUENCING", "ADMIN",
    "INTEGRITY", "BOUNDARIES",
)


# ── module-level guarantees ────────────────────────────────────────────────────

def test_module_imports_and_top_level_constants_exist():
    for name in _TOP_LEVEL_CONSTANTS:
        assert hasattr(md, name), f"missing top-level constant: {name}"


def test_every_constant_is_json_serializable():
    for name in _TOP_LEVEL_CONSTANTS:
        json.dumps(getattr(md, name))  # raises TypeError on any leak


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


def test_every_keyed_block_entry_key_matches_dict_key():
    for block_name in _KEYED_BLOCKS:
        block = getattr(md, block_name)
        for k, v in block.items():
            assert v["key"] == k, f"{block_name}[{k!r}] has mismatched key {v.get('key')!r}"


# ── ZERO currency / dollar-figure patterns anywhere (extra scrutiny: this
#    corpus is explicitly about money) ─────────────────────────────────────────

def test_no_currency_symbols_anywhere_in_source():
    for symbol in ("$", "£", "€", "¥", "₹", "¢", "₩"):
        assert symbol not in _SOURCE, f"currency symbol {symbol!r} leaked into the corpus"


def test_no_currency_amounts_in_serialized_corpus():
    # Scan the fully-serialized corpus for a number adjacent to any money word.
    blob = "\n".join(
        json.dumps(getattr(md, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    money_words = r"(?:dollars?|usd|cad|eur|euros?|gbp|pounds?|cents?|aud|fees?|figures?|amounts?)"
    assert not re.search(rf"\d[\d,\.]*\s*{money_words}", blob), "digit-then-money-word amount found"
    assert not re.search(rf"{money_words}\s*\d", blob), "money-word-then-digit amount found"


def test_zero_digits_anywhere_in_serialized_corpus():
    # This domain is explicitly about money, so this corpus goes further than
    # its siblings: not merely "no digit next to a money word", but no digit
    # anywhere at all in any of the encoded knowledge. Stream counts and
    # sequencing advice are spelled out in words ("three to five") specifically
    # so this stricter bar can hold with zero exceptions.
    # ensure_ascii=False so em-dashes and other non-ASCII characters are not
    # escaped into \uXXXX sequences, which would contain digits of their own
    # and produce false positives unrelated to any actual number in the text.
    blob = "\n".join(
        json.dumps(getattr(md, name), ensure_ascii=False) for name in _TOP_LEVEL_CONSTANTS
    )
    assert not re.search(r"\d", blob), "a digit was found somewhere in the corpus"


def test_mo_doctrine_bans_income_projections():
    text = json.dumps(md.MO_DOCTRINE).lower()
    assert "income projection" in text
    assert "dollar figure" in text


def test_no_signable_or_assured_income_language():
    blob = "\n".join(
        json.dumps(getattr(md, name)) for name in _TOP_LEVEL_CONSTANTS
    ).lower()
    for banned in ("guaranteed income", "you will earn", "expect to make"):
        assert banned not in blob, f"assured-income language leaked into corpus: {banned!r}"


# ── REVENUE_STREAM_TAXONOMY coverage ───────────────────────────────────────────

_EXPECTED_STREAM_KEYS = {
    "streaming_royalties", "live_performance", "merchandise", "sync_licensing",
    "publishing_royalties", "direct_fan_support", "teaching_and_session_work",
    "content_monetization", "brand_partnerships", "grants",
}


def test_all_ten_revenue_streams_present_with_full_schema():
    assert set(md.REVENUE_STREAM_TAXONOMY) == _EXPECTED_STREAM_KEYS
    assert len(md.REVENUE_STREAM_TAXONOMY) == 10
    for key, rec in md.REVENUE_STREAM_TAXONOMY.items():
        assert rec["key"] == key
        for field in ("description", "mechanism", "prerequisites",
                      "payment_pattern", "owning_department"):
            assert field in rec, f"{key} missing {field}"
        assert isinstance(rec["prerequisites"], list) and rec["prerequisites"]
        pattern = rec["payment_pattern"]
        assert isinstance(pattern, (str, list)) and pattern
        dept = rec["owning_department"]
        assert dept is None or isinstance(dept, (str, list))


def test_live_performance_owned_by_tour_commander():
    assert md.REVENUE_STREAM_TAXONOMY["live_performance"]["owning_department"] == "tour-commander"


def test_live_performance_names_merch_routing_and_draw():
    text = md.REVENUE_STREAM_TAXONOMY["live_performance"]["description"].lower()
    assert "merch" in text
    assert "routing" in text
    assert "draw" in text


def test_sync_licensing_owned_by_ink_and_air():
    assert md.REVENUE_STREAM_TAXONOMY["sync_licensing"]["owning_department"] == "ink-and-air"


def test_publishing_royalties_cross_refs_ink_and_air_and_ledger_lock():
    dept = md.REVENUE_STREAM_TAXONOMY["publishing_royalties"]["owning_department"]
    assert "ink-and-air" in dept
    assert "ledger-lock" in dept


def test_brand_partnerships_owned_by_brand_connect():
    assert md.REVENUE_STREAM_TAXONOMY["brand_partnerships"]["owning_department"] == "brand-connect"


def test_grants_owned_by_fund_phantom():
    assert md.REVENUE_STREAM_TAXONOMY["grants"]["owning_department"] == "fund-phantom"


def test_streaming_royalties_notes_rarely_sufficient_alone():
    text = md.REVENUE_STREAM_TAXONOMY["streaming_royalties"]["description"].lower()
    assert "rarely sufficient" in text or "rarely enough" in text


def test_teaching_and_session_work_is_audience_independent_in_taxonomy():
    text = md.REVENUE_STREAM_TAXONOMY["teaching_and_session_work"]["description"].lower()
    assert "no existing audience" in text or "without requiring an existing audience" in text


def test_direct_fan_support_covers_both_subscriptions_and_crowdfunding():
    text = json.dumps(md.REVENUE_STREAM_TAXONOMY["direct_fan_support"]).lower()
    assert "subscription" in text
    assert "crowdfunding" in text
    assert "recurring" in text


# ── DIVERSIFICATION coverage ────────────────────────────────────────────────────

_EXPECTED_DIVERSIFICATION_KEYS = {
    "stream_count_range", "no_catastrophic_single_point",
    "predictable_vs_lumpy_balance", "compounding_relationships",
    "start_small_then_add", "match_artist_strengths",
}


def test_all_diversification_keys_present():
    assert set(md.DIVERSIFICATION) == _EXPECTED_DIVERSIFICATION_KEYS


def test_stream_count_range_is_three_to_five():
    text = md.DIVERSIFICATION["stream_count_range"]["description"].lower()
    assert "three to five" in text


def test_no_single_stream_should_be_catastrophic():
    text = md.DIVERSIFICATION["no_catastrophic_single_point"]["description"].lower()
    assert "catastrophic" in text


def test_compounding_relationships_names_all_three_explicitly():
    text = md.DIVERSIFICATION["compounding_relationships"]["description"].lower()
    assert "live performance drives merch" in text
    assert "streaming attracts sync-licensing" in text
    assert "teaching builds session-work credibility" in text


def test_start_small_then_add_sequencing_advice():
    text = md.DIVERSIFICATION["start_small_then_add"]["description"].lower()
    assert "two to three" in text
    assert "master" in text


def test_match_artist_strengths_not_generic_template():
    text = md.DIVERSIFICATION["match_artist_strengths"]["description"].lower()
    assert "generic template" in text


# ── SEQUENCING coverage ─────────────────────────────────────────────────────────

def test_sequencing_has_both_categories():
    assert set(md.SEQUENCING) == {"audience_independent_streams", "audience_dependent_streams"}
    assert md.SEQUENCING["audience_independent_streams"]["category"] == "audience_independent"
    assert md.SEQUENCING["audience_dependent_streams"]["category"] == "audience_dependent"


def test_audience_independent_streams_is_teaching_and_session_work():
    rec = md.SEQUENCING["audience_independent_streams"]
    assert rec["streams"] == ["teaching_and_session_work"]
    text = rec["description"].lower()
    assert "day one" in text
    assert "no" in text and "audience" in text


def test_audience_dependent_streams_is_merch_subscriptions_streaming():
    rec = md.SEQUENCING["audience_dependent_streams"]
    assert set(rec["streams"]) == {"merchandise", "direct_fan_support", "streaming_royalties"}
    text = rec["description"].lower()
    assert "subscription" in text
    assert "merch" in text
    assert "streaming" in text
    assert "existing fanbase" in text


def test_sequencing_streams_reference_valid_taxonomy_keys():
    all_stream_keys = set(md.REVENUE_STREAM_TAXONOMY)
    for rec in md.SEQUENCING.values():
        for s in rec["streams"]:
            assert s in all_stream_keys, f"SEQUENCING references unknown stream {s!r}"


# ── ADMIN coverage ───────────────────────────────────────────────────────────────

_EXPECTED_ADMIN_KEYS = {
    "per_stream_registration_and_reporting", "sloppy_metadata_quietly_loses_money",
    "catalog_as_structured_asset",
}


def test_all_admin_keys_present():
    assert set(md.ADMIN) == _EXPECTED_ADMIN_KEYS


def test_sloppy_metadata_quietly_loses_money_doctrine_present():
    text = md.ADMIN["sloppy_metadata_quietly_loses_money"]["description"].lower()
    assert "sloppy metadata" in text
    assert "unclaimed" in text
    assert "quietly loses money" in text or "quietly lose money" in text


def test_catalog_as_structured_asset_cross_refs_ledger_lock():
    text = md.ADMIN["catalog_as_structured_asset"]["description"].lower()
    assert "ledger-lock" in text
    assert "structured asset" in text


# ── INTEGRITY coverage — the hardest rule in this corpus ────────────────────────

def test_integrity_keys_present():
    assert set(md.INTEGRITY) == {"never_states_a_dollar_figure", "how_much_gets_mechanism_and_it_varies"}


def test_never_a_dollar_figure_rule_is_non_empty_and_absolute():
    text = md.INTEGRITY["never_states_a_dollar_figure"]["description"].lower()
    assert text
    assert "never" in text
    assert "dollar figure" in text


def test_how_much_question_gets_artist_supplied_and_it_varies_framing():
    text = md.INTEGRITY["how_much_gets_mechanism_and_it_varies"]["description"]
    assert "[ARTIST-SUPPLIED]" in text
    assert "it varies" in text.lower()


# ── BOUNDARIES coverage ─────────────────────────────────────────────────────────

_EXPECTED_BOUNDARY_ROUTES = {
    "grant_application_execution": "fund-phantom",
    "brand_partnership_outreach": "brand-connect",
    "royalty_registration_and_collection": "ledger-lock",
    "sync_licensing_pitching": "ink-and-air",
    "booking_and_touring_execution": "tour-commander",
}


def test_boundaries_route_to_owning_departments_by_name():
    assert set(md.BOUNDARIES) == set(_EXPECTED_BOUNDARY_ROUTES)
    for key, dept in _EXPECTED_BOUNDARY_ROUTES.items():
        rec = md.BOUNDARIES[key]
        assert rec["owning_department"] == dept, f"{key} routes to wrong department"
        assert rec.get("what") and rec.get("mo_role")


def test_boundaries_state_mo_maps_but_does_not_execute():
    for key, rec in md.BOUNDARIES.items():
        text = rec["mo_role"].lower()
        assert "mo maps" in text, f"{key} mo_role does not state Mo's mapping-only role"
