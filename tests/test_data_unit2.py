"""
PROOF tests — Data Unit 2 (DOC-WRITER Option B service + wiring).

Locks the two replacement tools, permanently:

  lookup_analytics_doctrine — pure corpus read/filter over analytics_data,
    UNGATED (no env, no account); index mode with no filters; per-block
    filtering; a filter that matches nothing lands in not_found with value
    None (never guessed).

  build_analytics_doc_scaffold — OPTION B: COMPACT ingredients only, no prose,
    no model call (AST-enforced: the service imports no LLM SDK and contains
    no ``messages.create``). Two doc types:
      * metrics_readout — artist-supplied metric fields restated verbatim,
        applicable DIAGNOSIS_PAIRS KEYS (never a verdict), all
        INTERPRETATION_BANDS, dig-in questions; NEVER a computed percentage,
        ratio, or score.
      * stakeholder_stat_sheet — one named stakeholder's ``wants`` matched
        against artist-supplied numbers; unknown/missing stakeholder never
        silently defaulted.

  This unit OWNS the exact Data tool roster/count. NEVER asserts generated
  prose — scaffolds are structured; the Anthropic client is faked in the
  wiring tests.
"""
import ast
import asyncio
import importlib
import json
import pathlib
import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import analytics_data as ad
import data_oracle_service as svc
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
# lookup_analytics_doctrine — pure corpus read, ungated
# ═══════════════════════════════════════════════════════════════════════════════

def test_lookup_index_mode_lists_all_block_keys(monkeypatch):
    monkeypatch.delenv("DATA_ORACLE_WAREHOUSE_CONNECTED", raising=False)  # no gate exists
    res = _run(svc.lookup_analytics_doctrine())
    assert res["status"] == "ok"
    assert res["mode"] == "index"
    assert res["metric_keys"] == list(ad.METRIC_DEFINITIONS)
    assert res["band_keys"] == list(ad.INTERPRETATION_BANDS)
    assert res["source_keys"] == list(ad.SOURCE_BREAKDOWN)
    assert res["diagnosis_keys"] == list(ad.DIAGNOSIS_PAIRS)
    assert res["quality_keys"] == list(ad.QUALITY_VS_VANITY)
    assert res["stakeholder_keys"] == list(ad.STAKEHOLDER_FRAMING)
    assert res["data_doctrine"] == dict(ad.DATA_DOCTRINE)


def test_lookup_filters_each_block_and_returns_full_records():
    res = _run(svc.lookup_analytics_doctrine(
        metric_key="save_rate", band_key="skip_rate_high", source_key="editorial",
        diagnosis_key="high_streams_low_saves", quality_key="vanity_metrics",
        stakeholder_key="labels_and_ar"))
    assert res["mode"] == "filtered"
    assert res["metrics"][0]["key"] == "save_rate"
    assert res["bands"][0]["key"] == "skip_rate_high"
    assert res["sources"][0]["key"] == "editorial"
    assert res["diagnosis"][0]["key"] == "high_streams_low_saves"
    assert res["quality"][0]["key"] == "vanity_metrics"
    assert res["stakeholders"][0]["key"] == "labels_and_ar"
    assert res["not_found"] == []


def test_lookup_unknown_key_recorded_as_not_found_never_guessed():
    res = _run(svc.lookup_analytics_doctrine(metric_key="no_such_key"))
    assert res["metrics"] == []
    assert res["not_found"] == [{"filter": "metric_key", "value": "no_such_key", "match": None}]


def test_lookup_always_carries_data_doctrine_integrity_and_boundaries():
    res = _run(svc.lookup_analytics_doctrine(metric_key="stream"))
    assert "never_fabricate_numbers" in res["data_doctrine"]
    integrity_keys = {i["key"] for i in res["integrity"]}
    assert {"never_loop_or_incentivize_streams", "never_fabricate_numbers"} <= integrity_keys
    boundary_keys = {b["key"] for b in res["boundaries"]}
    assert "acting_on_insights" in boundary_keys

    # index mode carries the same standing framing too.
    idx = _run(svc.lookup_analytics_doctrine())
    assert idx["data_doctrine"] == res["data_doctrine"]
    assert idx["integrity"] == res["integrity"]
    assert idx["boundaries"] == res["boundaries"]


# ═══════════════════════════════════════════════════════════════════════════════
# build_analytics_doc_scaffold — metrics_readout
# ═══════════════════════════════════════════════════════════════════════════════

_FULL_METRICS_INPUTS = {
    "stream": 50000,
    "monthly_listeners": 8000,
    "saves": 3000,
    "followers": 1200,
    "save_rate": 0.06,
    "streams_per_listener_ratio": 6.25,
}


def test_metrics_readout_full_inputs_ready_all_sections_no_gaps():
    res = _run(svc.build_analytics_doc_scaffold("metrics_readout", _FULL_METRICS_INPUTS))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "metrics_readout"
    keys = [s["key"] for s in res["sections"]]
    assert "supplied_metrics" in keys
    assert "applicable_diagnosis_pairs" in keys
    assert "interpretation_bands" in keys
    assert "dig_in_questions" in keys
    assert res["missing"] == []


def test_metrics_readout_supplied_metrics_verbatim():
    res = _run(svc.build_analytics_doc_scaffold("metrics_readout", _FULL_METRICS_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "supplied_metrics")
    by_field = {f["field"]: f["value"] for f in section["fields"]}
    assert by_field["stream"] == 50000
    assert by_field["saves"] == 3000
    assert by_field["save_rate"] == 0.06  # verbatim — never recomputed by this tool


def test_metrics_readout_missing_fields_are_artist_supplied_markers():
    res = _run(svc.build_analytics_doc_scaffold("metrics_readout", {}))
    assert "[ARTIST-SUPPLIED:stream]" in res["missing"]
    assert "[ARTIST-SUPPLIED:saves]" in res["missing"]
    assert "[ARTIST-SUPPLIED:followers]" in res["missing"]
    section = next(s for s in res["sections"] if s["key"] == "supplied_metrics")
    assert all(f["value"].startswith("[ARTIST-SUPPLIED:") for f in section["fields"])


def test_metrics_readout_diagnosis_pairs_applicable_only_when_fields_supplied():
    # No fields supplied at all -> no diagnosis pairs are applicable.
    res_empty = _run(svc.build_analytics_doc_scaffold("metrics_readout", {}))
    empty_section = next(s for s in res_empty["sections"] if s["key"] == "applicable_diagnosis_pairs")
    assert empty_section["pairs"] == []

    # Both a streams figure and a saves figure supplied -> both directional
    # pattern KEYS surface for the agent to reason about (never a verdict).
    res = _run(svc.build_analytics_doc_scaffold(
        "metrics_readout", {"stream": 50000, "saves": 3000}))
    section = next(s for s in res["sections"] if s["key"] == "applicable_diagnosis_pairs")
    pair_keys = {p["key"] for p in section["pairs"]}
    assert {"high_streams_low_saves", "high_saves_low_streams"} <= pair_keys
    # followers_stay_listeners_fall requires followers + monthly_listeners, neither supplied.
    assert "followers_stay_listeners_fall" not in pair_keys


def test_metrics_readout_interpretation_bands_always_surfaces_all_bands():
    res = _run(svc.build_analytics_doc_scaffold("metrics_readout", _FULL_METRICS_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "interpretation_bands")
    assert {b["key"] for b in section["bands"]} == set(ad.INTERPRETATION_BANDS)
    # No bands are narrowed to "the one that applies" — that requires
    # arithmetic only the agent performs.
    res_empty = _run(svc.build_analytics_doc_scaffold("metrics_readout", {}))
    empty_section = next(s for s in res_empty["sections"] if s["key"] == "interpretation_bands")
    assert {b["key"] for b in empty_section["bands"]} == set(ad.INTERPRETATION_BANDS)


def test_metrics_readout_dig_in_questions_present_and_are_questions():
    res = _run(svc.build_analytics_doc_scaffold("metrics_readout", {}))
    section = next(s for s in res["sections"] if s["key"] == "dig_in_questions")
    assert len(section["questions"]) >= 3
    for q in section["questions"]:
        assert "?" in q


# CRITICAL INVARIANT: never a computed percentage, ratio, or score.
_BANNED_COMPUTED_KEY_RE = re.compile(
    r'"[a-z_]*(growth_pct|percentage|computed|delta|score|ratio_computed)[a-z_]*"\s*:\s*-?\d'
)


def test_metrics_readout_never_computes_a_number():
    scaffolds = [
        _run(svc.build_analytics_doc_scaffold("metrics_readout", _FULL_METRICS_INPUTS)),
        _run(svc.build_analytics_doc_scaffold("metrics_readout", {})),
        _run(svc.build_analytics_doc_scaffold("metrics_readout", {"stream": 1, "saves": 1})),
    ]
    for res in scaffolds:
        blob = json.dumps(res).lower()
        assert not _BANNED_COMPUTED_KEY_RE.search(blob), "computed numeric field leaked"
        for banned_key in ('"growth_pct"', '"score"', '"percentage"', '"total"', '"sum"'):
            assert banned_key not in blob


# ═══════════════════════════════════════════════════════════════════════════════
# build_analytics_doc_scaffold — stakeholder_stat_sheet
# ═══════════════════════════════════════════════════════════════════════════════

_VENUE_STAT_SHEET_INPUTS = {
    "stakeholder": "venues_and_agents",
    "listeners_in_their_city": "1,200 monthly listeners in Chicago",
    "draw_evidence": "sold out a 300-cap room last spring",
}


def test_stakeholder_stat_sheet_full_inputs_ready_wants_matched_verbatim():
    res = _run(svc.build_analytics_doc_scaffold("stakeholder_stat_sheet", _VENUE_STAT_SHEET_INPUTS))
    assert res["status"] == "scaffold_ready"
    section = next(s for s in res["sections"] if s["key"] == "stakeholder_wants")
    assert section["stakeholder"] == "venues_and_agents"
    by_want = {w["want"]: w["value"] for w in section["wants"]}
    assert by_want["listeners_in_their_city"] == _VENUE_STAT_SHEET_INPUTS["listeners_in_their_city"]
    assert by_want["draw_evidence"] == _VENUE_STAT_SHEET_INPUTS["draw_evidence"]
    assert res["missing"] == []


def test_stakeholder_stat_sheet_labels_and_ar_wants():
    res = _run(svc.build_analytics_doc_scaffold("stakeholder_stat_sheet", {
        "stakeholder": "labels_and_ar",
        "growth_trend": "up 15% quarter over quarter",  # artist's own words, verbatim
        "save_rate": 0.06,
    }))
    section = next(s for s in res["sections"] if s["key"] == "stakeholder_wants")
    by_want = {w["want"]: w["value"] for w in section["wants"]}
    assert by_want["growth_trend"] == "up 15% quarter over quarter"
    assert by_want["save_rate"] == 0.06
    assert "[ARTIST-SUPPLIED:source_mix]" in res["missing"]
    assert "[ARTIST-SUPPLIED:follower_ratio]" in res["missing"]


def test_stakeholder_stat_sheet_missing_stakeholder_is_gap_marker():
    res = _run(svc.build_analytics_doc_scaffold("stakeholder_stat_sheet", {}))
    assert res["status"] == "scaffold_ready"
    assert "[ARTIST-SUPPLIED:stakeholder]" in res["missing"]
    assert res["sections"] == []
    note = next(n for n in res["notes"] if n["section"] == "stakeholder")
    assert "note" in note


def test_stakeholder_stat_sheet_unknown_stakeholder_never_silently_defaulted():
    res = _run(svc.build_analytics_doc_scaffold(
        "stakeholder_stat_sheet", {"stakeholder": "streaming_platforms"}))
    assert res["status"] == "scaffold_ready"
    assert res["sections"] == []  # never guessed a stakeholder to fall back on
    note = next(n for n in res["notes"] if n["section"] == "stakeholder")
    assert note["error"] == "unknown_stakeholder"
    assert "streaming_platforms" in note["note"]


def test_stakeholder_stat_sheet_missing_want_fields_are_artist_supplied_markers():
    res = _run(svc.build_analytics_doc_scaffold(
        "stakeholder_stat_sheet", {"stakeholder": "venues_and_agents"}))
    assert "[ARTIST-SUPPLIED:listeners_in_their_city]" in res["missing"]
    assert "[ARTIST-SUPPLIED:draw_evidence]" in res["missing"]


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-doc-type invariants
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_doc_type_returns_structured_error():
    res = _run(svc.build_analytics_doc_scaffold("mystery_doc", {}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(svc.DOC_TYPES)


def test_gap_markers_aggregate_across_both_doc_types():
    for doc_type in svc.DOC_TYPES:
        res = _run(svc.build_analytics_doc_scaffold(doc_type, {}))
        assert res["status"] == "scaffold_ready"
        assert isinstance(res["missing"], list)
        assert len(res["missing"]) == len(set(res["missing"])), "missing[] must be deduped"


def test_missing_dedup_within_a_single_scaffold():
    # metrics_readout has six distinct metric fields; calling twice with the
    # same empty inputs must not produce duplicate markers within one response.
    res = _run(svc.build_analytics_doc_scaffold("metrics_readout", {}))
    assert len(res["missing"]) == len(set(res["missing"]))
    assert len(res["missing"]) == len(ad.METRIC_DEFINITIONS)


def test_service_layer_is_entity_wall_clean():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


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

def test_data_tool_roster_is_exactly_the_two_docwriter_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.DATA_ORACLE_TOOLS]
    assert names == ["lookup_analytics_doctrine", "build_analytics_doc_scaffold"]


def test_lookup_tool_enums_match_the_corpus(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    lookup = next(t for t in m.DATA_ORACLE_TOOLS if t["name"] == "lookup_analytics_doctrine")
    props = lookup["input_schema"]["properties"]
    assert props["metric_key"]["enum"] == list(ad.METRIC_DEFINITIONS)
    assert props["band_key"]["enum"] == list(ad.INTERPRETATION_BANDS)
    assert props["source_key"]["enum"] == list(ad.SOURCE_BREAKDOWN)
    assert props["diagnosis_key"]["enum"] == list(ad.DIAGNOSIS_PAIRS)
    assert props["quality_key"]["enum"] == list(ad.QUALITY_VS_VANITY)
    assert props["stakeholder_key"]["enum"] == list(ad.STAKEHOLDER_FRAMING)
    assert "required" not in lookup["input_schema"]  # all filters optional


def test_build_tool_requires_doc_type_with_docwriter_enum(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    build = next(t for t in m.DATA_ORACLE_TOOLS if t["name"] == "build_analytics_doc_scaffold")
    assert build["input_schema"]["required"] == ["doc_type"]
    assert build["input_schema"]["properties"]["doc_type"]["enum"] == list(svc.DOC_TYPES)


def test_dispatch_not_gated_and_returns_three_tuple(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("DATA_ORACLE_WAREHOUSE_CONNECTED", raising=False)
    result, summary, dwnc = _run(m._execute_data_oracle_tool(
        "build_analytics_doc_scaffold",
        {"doc_type": "metrics_readout", "inputs": {"stream": 1}},
        "artist-1"))
    assert result["status"] == "scaffold_ready"
    assert dwnc is False  # gate retired — always False
    assert "section(s)" in summary["result"]


def test_dispatch_unknown_tool_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, dwnc = _run(m._execute_data_oracle_tool("nonexistent_tool", {}, "a"))
    assert result["error"] == "unknown_tool"
    assert dwnc is False


def test_service_roster_is_exactly_the_two_docwriter_functions():
    # This unit's service module exposes exactly the two DOC-WRITER entry
    # points and nothing else callable from the old mock+gate surface — the
    # roster/tool-count tests above already own the exact DATA_ORACLE_TOOLS
    # contents, and the entity-wall + AST checks above cover the rest.
    public_callables = {
        n for n in dir(svc)
        if not n.startswith("_") and callable(getattr(svc, n)) and n != "analytics_data"
    }
    assert public_callables == {"lookup_analytics_doctrine", "build_analytics_doc_scaffold"}
