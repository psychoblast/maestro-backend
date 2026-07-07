"""
PROOF tests — Kai Unit 2 (DOC-WRITER Option B service + wiring).

Locks the two replacement tools, permanently:

  lookup_digital_marketing_doctrine — pure corpus read/filter over
    digital_marketing_data, UNGATED (no env, no account); index mode with no
    filters; per-block filtering; a filter that matches nothing lands in
    not_found with value None (never guessed).

  build_marketing_doc_scaffold — OPTION B: COMPACT ingredients only, no
    prose, no model call (AST-enforced: the service imports no LLM SDK and
    contains no ``messages.create``). Two doc types:
      * campaign_plan — the CHANNEL_SEQUENCE sequencing order verbatim
        (always returned even with no channels_in_place), artist-supplied
        channels_in_place validated against the four recognized stage names
        (unrecognized values noted as unknown_channel_stage, never silently
        accepted), BUDGET_MECHANICS's testing approach verbatim, a
        MEASUREMENT checklist, and a budget section that is ALWAYS an
        [ARTIST-SUPPLIED:budget] marker, never a figure.
      * ad_test_brief — a creative-variants checklist, kill/scale criteria
        (BUDGET_MECHANICS verbatim), a warm-audience inventory question set,
        and the same budget-out-of-scope invariant.

  This unit OWNS the exact Kai tool roster/count. NEVER asserts generated
  prose — scaffolds are structured; the Anthropic client is faked in the
  wiring tests. The single most important test in this unit: NEITHER
  scaffold doc type ever echoes a numeric budget/spend figure, even when one
  is supplied in inputs.
"""
import ast
import asyncio
import importlib
import json
import pathlib
import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import digital_marketing_data as dmd
import grid_prophet_service as svc
from entity_wall_terms import assert_no_forbidden_terms


def _run(coro):
    return asyncio.run(coro)


# ── fake Anthropic SDK shapes (wiring tests) ───────────────────────────────────

class _Block:
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type = type
        self.text = text
        self.name = name
        self.input = input
        self.id = id


class _Resp:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class _FakeStream:
    def __init__(self, text):
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def _gen():
            yield self._text
        return _gen()


def _load_main(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("BANK_CONSULT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        import main as m
        importlib.reload(m)
    return m


def _parse_sse(body: str) -> list:
    events = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


# ═══════════════════════════════════════════════════════════════════════════════
# lookup_digital_marketing_doctrine — pure corpus read, ungated
# ═══════════════════════════════════════════════════════════════════════════════

def test_lookup_index_mode_lists_all_block_keys(monkeypatch):
    monkeypatch.delenv("GRID_PROPHET_ACCOUNT_CONNECTED", raising=False)  # no gate exists
    res = _run(svc.lookup_digital_marketing_doctrine())
    assert res["status"] == "ok"
    assert res["mode"] == "index"
    assert res["sequence_keys"] == list(dmd.CHANNEL_SEQUENCE)
    assert res["proof_keys"] == list(dmd.ORGANIC_PROOF_FIRST)
    assert res["platform_keys"] == list(dmd.PLATFORM_SELECTION)
    assert res["budget_keys"] == list(dmd.BUDGET_MECHANICS)
    assert res["measurement_keys"] == list(dmd.MEASUREMENT)
    assert res["momentum_keys"] == list(dmd.FIRST_72_HOURS)
    assert res["kai_doctrine"] == dict(dmd.KAI_DOCTRINE)


def test_lookup_filters_each_block_and_returns_full_records():
    res = _run(svc.lookup_digital_marketing_doctrine(
        sequence_key="streaming_platform_optimization", proof_key="spark_ad_pattern",
        platform_key="warm_before_cold", budget_key="kill_fast",
        measurement_key="save_rate", momentum_key="pre_save_campaigns_build_early_signal"))
    assert res["mode"] == "filtered"
    assert res["sequence"][0]["key"] == "streaming_platform_optimization"
    assert res["proof"][0]["key"] == "spark_ad_pattern"
    assert res["platform"][0]["key"] == "warm_before_cold"
    assert res["budget"][0]["key"] == "kill_fast"
    assert res["measurement"][0]["key"] == "save_rate"
    assert res["momentum"][0]["key"] == "pre_save_campaigns_build_early_signal"
    assert res["not_found"] == []


def test_lookup_unknown_key_recorded_as_not_found_never_guessed():
    res = _run(svc.lookup_digital_marketing_doctrine(budget_key="no_such_key"))
    assert res["budget"] == []
    assert res["not_found"] == [{"filter": "budget_key", "value": "no_such_key", "match": None}]


def test_lookup_multiple_unknown_keys_all_recorded():
    res = _run(svc.lookup_digital_marketing_doctrine(
        sequence_key="nope", proof_key="also_nope"))
    values = {nf["value"] for nf in res["not_found"]}
    assert values == {"nope", "also_nope"}


def test_lookup_always_carries_kai_doctrine_integrity_and_boundaries():
    res = _run(svc.lookup_digital_marketing_doctrine(sequence_key="email"))
    assert "sequence_before_spend" in res["kai_doctrine"]
    integrity_keys = {i["key"] for i in res["integrity"]}
    assert "never_buy_streams_or_followers" in integrity_keys
    boundary_keys = {b["key"] for b in res["boundaries"]}
    assert "press_and_earned_media" in boundary_keys

    # Doctrine/integrity/boundaries ride through in index mode too.
    idx = _run(svc.lookup_digital_marketing_doctrine())
    assert idx["kai_doctrine"] == res["kai_doctrine"]
    assert idx["integrity"] == res["integrity"]
    assert idx["boundaries"] == res["boundaries"]


# ═══════════════════════════════════════════════════════════════════════════════
# build_marketing_doc_scaffold — campaign_plan
# ═══════════════════════════════════════════════════════════════════════════════

_FULL_CAMPAIGN_INPUTS = {
    "channels_in_place": ["streaming_platform_optimization", "organic_short_form_content"],
}


def test_campaign_plan_full_inputs_ready_all_sections():
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", _FULL_CAMPAIGN_INPUTS))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "campaign_plan"
    keys = [s["key"] for s in res["sections"]]
    assert "sequencing_order" in keys
    assert "channels_in_place" in keys
    assert "testing_approach" in keys
    assert "measurement_checklist" in keys
    assert "budget" in keys
    assert res["missing"] == []


def test_campaign_plan_sequencing_order_matches_corpus_exactly():
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", _FULL_CAMPAIGN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "sequencing_order")
    assert section["order"] == dmd.CHANNEL_SEQUENCE["sequencing_order"]["order"]
    assert section["description"] == dmd.CHANNEL_SEQUENCE["sequencing_order"]["description"]


def test_campaign_plan_missing_channels_in_place_is_gap_marker_but_order_still_returned():
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", {}))
    assert "[ARTIST-SUPPLIED:channels_in_place]" in res["missing"]
    # The full sequencing order is STILL returned even with no channels_in_place.
    section = next(s for s in res["sections"] if s["key"] == "sequencing_order")
    assert section["order"] == dmd.CHANNEL_SEQUENCE["sequencing_order"]["order"]
    channels_section = next(s for s in res["sections"] if s["key"] == "channels_in_place")
    assert channels_section["declared"] == []
    assert channels_section["recognized"] == []


def test_campaign_plan_recognized_channels_in_place_rides_through():
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", _FULL_CAMPAIGN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "channels_in_place")
    assert section["recognized"] == [
        "streaming_platform_optimization", "organic_short_form_content"]
    assert section["not_yet_in_place"] == ["email", "paid_promotion"]
    assert section["unknown_channel_stage"] == []


def test_campaign_plan_unknown_channel_stage_never_silently_accepted():
    inp = {"channels_in_place": ["streaming_platform_optimization", "bought_followers_scheme"]}
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", inp))
    section = next(s for s in res["sections"] if s["key"] == "channels_in_place")
    assert section["recognized"] == ["streaming_platform_optimization"]
    assert section["unknown_channel_stage"] == ["bought_followers_scheme"]
    error_note = next(n for n in res["notes"] if n.get("error") == "unknown_channel_stage")
    assert "bought_followers_scheme" in error_note["unknown_channel_stage"]


def test_campaign_plan_non_list_channels_in_place_treated_as_missing():
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", {"channels_in_place": "email"}))
    assert "[ARTIST-SUPPLIED:channels_in_place]" in res["missing"]
    section = next(s for s in res["sections"] if s["key"] == "channels_in_place")
    assert section["declared"] == []


def test_campaign_plan_testing_approach_matches_corpus_verbatim():
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", _FULL_CAMPAIGN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "testing_approach")
    assert section["test_multiple_creatives_simultaneously"] == (
        dmd.BUDGET_MECHANICS["test_multiple_creatives_simultaneously"]["description"])
    assert section["kill_fast"] == dmd.BUDGET_MECHANICS["kill_fast"]["description"]


def test_campaign_plan_measurement_checklist_present():
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", _FULL_CAMPAIGN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "measurement_checklist")
    metric_keys = {m["key"] for m in section["metrics"]}
    assert metric_keys == {"save_rate", "follower_add_rate", "cost_per_engaged_listener"}
    assert section["fake_growth_warning"] == (
        dmd.MEASUREMENT["streams_without_saves_is_fake_growth_warning"]["description"])


# ═══════════════════════════════════════════════════════════════════════════════
# build_marketing_doc_scaffold — ad_test_brief
# ═══════════════════════════════════════════════════════════════════════════════

def test_ad_test_brief_all_sections_present():
    res = _run(svc.build_marketing_doc_scaffold("ad_test_brief", {}))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "ad_test_brief"
    keys = [s["key"] for s in res["sections"]]
    assert "creative_variants_checklist" in keys
    assert "kill_scale_criteria" in keys
    assert "warm_audience_inventory" in keys
    assert "budget" in keys


def test_ad_test_brief_creative_variants_checklist_is_a_list_derived_from_corpus():
    res = _run(svc.build_marketing_doc_scaffold("ad_test_brief", {}))
    section = next(s for s in res["sections"] if s["key"] == "creative_variants_checklist")
    assert isinstance(section["items"], list) and section["items"]
    assert section["source"] == (
        dmd.BUDGET_MECHANICS["test_multiple_creatives_simultaneously"]["description"])


def test_ad_test_brief_kill_scale_criteria_verbatim():
    res = _run(svc.build_marketing_doc_scaffold("ad_test_brief", {}))
    section = next(s for s in res["sections"] if s["key"] == "kill_scale_criteria")
    assert section["kill_fast"] == dmd.BUDGET_MECHANICS["kill_fast"]["description"]
    assert section["scale_only_what_already_works"] == (
        dmd.BUDGET_MECHANICS["scale_only_what_already_works"]["description"])


def test_ad_test_brief_warm_audience_inventory_is_questions_not_corpus_data():
    res = _run(svc.build_marketing_doc_scaffold("ad_test_brief", {}))
    section = next(s for s in res["sections"] if s["key"] == "warm_audience_inventory")
    assert isinstance(section["questions"], list) and len(section["questions"]) >= 3
    for q in section["questions"]:
        assert "?" in q
    # The questions themselves are NOT present verbatim as corpus dict keys.
    assert section["questions"] != list(dmd.PLATFORM_SELECTION)
    assert section["source"] == dmd.PLATFORM_SELECTION["warm_before_cold"]["description"]


# ═══════════════════════════════════════════════════════════════════════════════
# THE CRITICAL INVARIANT — never a numeric budget/spend figure, ever
# ═══════════════════════════════════════════════════════════════════════════════

_NUMERIC_MONEY_RE = re.compile(r'"[a-z_]*(budget|spend)[a-z_]*"\s*:\s*-?\d')


def test_campaign_plan_never_echoes_a_supplied_numeric_budget():
    inputs_variants = [
        {"channels_in_place": ["email"], "budget": 5000},
        {"channels_in_place": ["email"], "spend": 250.50},
        {"channels_in_place": ["email"], "ad_spend": "1000"},
        {"channels_in_place": ["email"], "monthly_budget": 999999},
        {},
    ]
    for inp in inputs_variants:
        res = _run(svc.build_marketing_doc_scaffold("campaign_plan", inp))
        blob = json.dumps(res)
        assert not _NUMERIC_MONEY_RE.search(blob), f"numeric budget leaked for inputs={inp}"
        for supplied_value in ("5000", "250.5", "1000", "999999"):
            if supplied_value in json.dumps(inp):
                assert supplied_value not in blob, (
                    f"supplied budget figure {supplied_value!r} leaked into scaffold")


def test_ad_test_brief_never_echoes_a_supplied_numeric_budget():
    inputs_variants = [
        {"budget": 12345},
        {"ad_spend": 777},
        {"budget": "10000 dollars a week"},
        {},
    ]
    for inp in inputs_variants:
        res = _run(svc.build_marketing_doc_scaffold("ad_test_brief", inp))
        blob = json.dumps(res)
        assert not _NUMERIC_MONEY_RE.search(blob), f"numeric budget leaked for inputs={inp}"
        for supplied_value in ("12345", "777", "10000"):
            if supplied_value in json.dumps(inp):
                assert supplied_value not in blob, (
                    f"supplied budget figure {supplied_value!r} leaked into scaffold")


def test_both_doc_types_budget_section_is_always_artist_supplied_marker():
    for doc_type, inputs in (
        ("campaign_plan", {"channels_in_place": ["email"], "budget": 42}),
        ("ad_test_brief", {"budget": 42}),
    ):
        res = _run(svc.build_marketing_doc_scaffold(doc_type, inputs))
        section = next(s for s in res["sections"] if s["key"] == "budget")
        assert section["marker"] == "[ARTIST-SUPPLIED:budget]"
        assert "42" not in json.dumps(section)


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-doc-type invariants
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_doc_type_returns_structured_error():
    res = _run(svc.build_marketing_doc_scaffold("mystery_doc", {}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(svc.DOC_TYPES)
    assert svc.DOC_TYPES == ("campaign_plan", "ad_test_brief")


def test_missing_dedup_across_both_doc_types():
    for doc_type in svc.DOC_TYPES:
        res = _run(svc.build_marketing_doc_scaffold(doc_type, {}))
        assert res["status"] == "scaffold_ready"
        assert isinstance(res["missing"], list)
        assert len(res["missing"]) == len(set(res["missing"])), "missing[] must be deduped"


def test_missing_dedup_even_with_repeated_bad_input_shapes():
    # Calling twice with the same missing-triggering input must not duplicate markers.
    res = _run(svc.build_marketing_doc_scaffold("campaign_plan", {"channels_in_place": None}))
    assert res["missing"].count("[ARTIST-SUPPLIED:channels_in_place]") == 1


def test_service_layer_is_entity_wall_clean():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


def test_header_carries_kai_doctrine_on_both_doc_types():
    for doc_type, inputs in (("campaign_plan", _FULL_CAMPAIGN_INPUTS), ("ad_test_brief", {})):
        res = _run(svc.build_marketing_doc_scaffold(doc_type, inputs))
        header = res["header"]
        assert header["sequence_before_spend"] == dmd.KAI_DOCTRINE["sequence_before_spend"]
        assert header["organic_proof_first"] == dmd.KAI_DOCTRINE["organic_proof_first"]
        assert header["never_buys_growth"] == dmd.KAI_DOCTRINE["never_buys_growth"]


# ═══════════════════════════════════════════════════════════════════════════════
# AST — the service imports no LLM SDK and never calls messages.create
# ═══════════════════════════════════════════════════════════════════════════════

def test_service_imports_no_anthropic_and_no_messages_create():
    source = pathlib.Path(svc.__file__).read_text(encoding="utf-8")
    assert "messages.create" not in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "anthropic" not in name.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Roster / tool counts (THIS UNIT OWNS THEM) + dispatch wiring
# ═══════════════════════════════════════════════════════════════════════════════

def test_kai_tool_roster_is_exactly_the_two_docwriter_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.GRID_PROPHET_TOOLS]
    assert names == ["lookup_digital_marketing_doctrine", "build_marketing_doc_scaffold"]
    assert len(m.GRID_PROPHET_TOOLS) == 2


def test_lookup_tool_enums_match_the_corpus(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    lookup = next(t for t in m.GRID_PROPHET_TOOLS if t["name"] == "lookup_digital_marketing_doctrine")
    props = lookup["input_schema"]["properties"]
    assert props["sequence_key"]["enum"] == list(dmd.CHANNEL_SEQUENCE)
    assert props["proof_key"]["enum"] == list(dmd.ORGANIC_PROOF_FIRST)
    assert props["platform_key"]["enum"] == list(dmd.PLATFORM_SELECTION)
    assert props["budget_key"]["enum"] == list(dmd.BUDGET_MECHANICS)
    assert props["measurement_key"]["enum"] == list(dmd.MEASUREMENT)
    assert props["momentum_key"]["enum"] == list(dmd.FIRST_72_HOURS)
    assert "required" not in lookup["input_schema"]  # all filters optional


def test_build_tool_requires_doc_type_with_docwriter_enum(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    build = next(t for t in m.GRID_PROPHET_TOOLS if t["name"] == "build_marketing_doc_scaffold")
    assert build["input_schema"]["required"] == ["doc_type"]
    assert build["input_schema"]["properties"]["doc_type"]["enum"] == list(svc.DOC_TYPES)


def test_dispatch_not_gated_and_returns_three_tuple(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("GRID_PROPHET_ACCOUNT_CONNECTED", raising=False)
    result, summary, snc = _run(m._execute_grid_prophet_tool(
        "build_marketing_doc_scaffold",
        {"doc_type": "campaign_plan", "inputs": {"channels_in_place": ["email"]}},
        "artist-1"))
    assert result["status"] == "scaffold_ready"
    assert snc is False  # gate retired — always False
    assert "section(s)" in summary["result"]


def test_dispatch_unknown_tool_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, snc = _run(m._execute_grid_prophet_tool("nonexistent_tool", {}, "a"))
    assert result["error"] == "unknown_tool"
    assert snc is False


def test_service_roster_is_exactly_the_two_docwriter_functions():
    # This unit's service module exposes exactly the two DOC-WRITER entry
    # points and nothing else callable from the old mock+gate surface — the
    # roster/tool-count tests above already own the exact GRID_PROPHET_TOOLS
    # contents, and the entity-wall + AST checks above cover the rest.
    public_callables = {
        n for n in dir(svc)
        if not n.startswith("_") and callable(getattr(svc, n)) and n != "digital_marketing_data"
    }
    assert public_callables == {"lookup_digital_marketing_doctrine", "build_marketing_doc_scaffold"}
