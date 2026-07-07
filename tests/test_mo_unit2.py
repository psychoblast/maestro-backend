"""
PROOF tests — Mo Unit 2 (DOC-WRITER Option B service + wiring).

Locks the two replacement tools, permanently:

  lookup_monetization_doctrine — pure corpus read/filter over
    monetization_data, UNGATED (no env, no account); index mode with no
    filters; per-block filtering; a filter that matches nothing lands in
    not_found with value None (never guessed).

  build_monetization_doc_scaffold — OPTION B: COMPACT ingredients only, no
    prose, no model call (AST-enforced: the service imports no LLM SDK and
    contains no ``messages.create``). Two doc types:
      * revenue_map — the artist's current streams matched against the full
        taxonomy; every other taxonomy stream surfaced as an addressable_next
        candidate, stage-aware (audience_independent always addressable,
        audience_dependent only once audience_stage == has_audience,
        unclassified streams have no known restriction); DIVERSIFICATION's
        compounding_relationships / no_catastrophic_single_point doctrine
        verbatim.
      * diversification_plan — 2-3 next-stream candidates (same stage-aware
        addressability), each carrying prerequisites + owning_department
        verbatim, plus start_small_then_add doctrine verbatim.

  CRITICAL INVARIANT: neither doc type may EVER compute, sum, project, or
  estimate a numeric income figure of any kind — this domain is explicitly
  about money, so this unit tests that invariant harder than any sibling.

  This unit OWNS the exact Mo tool roster/count. NEVER asserts generated
  prose — scaffolds are structured; the Anthropic client is faked in the
  wiring-adjacent roster tests below.
"""
import ast
import asyncio
import importlib
import json
import pathlib
import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import monetization_data as md
import mobile_monetize_service as svc
from entity_wall_terms import assert_no_forbidden_terms


def _run(coro):
    return asyncio.run(coro)


def _load_main(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("BANK_CONSULT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        # Same '/data'-rebake guard as test_cree_unit2 / test_nadia_unit3 / test_lex_unit2 /
        # test_miles_unit2.
        import booking_service, phase4_service, pitch_service
        import pr_service, release_service, social_service
        for _svc_mod in (booking_service, phase4_service, pitch_service,
                         pr_service, release_service, social_service):
            importlib.reload(_svc_mod)
        import main as m
        importlib.reload(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════════
# lookup_monetization_doctrine — pure corpus read, ungated
# ═══════════════════════════════════════════════════════════════════════════════

def test_lookup_index_mode_lists_all_block_keys(monkeypatch):
    monkeypatch.delenv("MOBILE_MONETIZE_CONNECTED", raising=False)  # no gate exists
    res = _run(svc.lookup_monetization_doctrine())
    assert res["status"] == "ok"
    assert res["mode"] == "index"
    assert res["stream_keys"] == list(md.REVENUE_STREAM_TAXONOMY)
    assert res["diversification_keys"] == list(md.DIVERSIFICATION)
    assert res["sequencing_keys"] == list(md.SEQUENCING)
    assert res["admin_keys"] == list(md.ADMIN)
    assert res["mo_doctrine"] == dict(md.MO_DOCTRINE)


def test_lookup_filters_each_block_and_returns_full_records():
    res = _run(svc.lookup_monetization_doctrine(
        stream_key="live_performance", diversification_key="stream_count_range",
        sequencing_key="audience_independent_streams", admin_key="catalog_as_structured_asset"))
    assert res["mode"] == "filtered"
    assert res["streams"][0]["key"] == "live_performance"
    assert res["diversification"][0]["key"] == "stream_count_range"
    assert res["sequencing"][0]["key"] == "audience_independent_streams"
    assert res["admin"][0]["key"] == "catalog_as_structured_asset"
    assert res["not_found"] == []


def test_lookup_unknown_key_recorded_as_not_found_never_guessed():
    res = _run(svc.lookup_monetization_doctrine(stream_key="no_such_stream"))
    assert res["streams"] == []
    assert res["not_found"] == [{"filter": "stream_key", "value": "no_such_stream", "match": None}]


def test_lookup_always_carries_mo_doctrine_integrity_and_boundaries():
    res = _run(svc.lookup_monetization_doctrine(stream_key="live_performance"))
    boundary_keys = {b["key"] for b in res["boundaries"]}
    assert {"grant_application_execution", "brand_partnership_outreach",
            "royalty_registration_and_collection", "sync_licensing_pitching",
            "booking_and_touring_execution"} <= boundary_keys
    assert "no_income_projections" in res["mo_doctrine"]
    integrity_keys = {i["key"] for i in res["integrity"]}
    assert "never_states_a_dollar_figure" in integrity_keys

    # Also present on the no-filter index response.
    res2 = _run(svc.lookup_monetization_doctrine())
    assert "no_income_projections" in res2["mo_doctrine"]
    assert {b["key"] for b in res2["boundaries"]} == boundary_keys


# ═══════════════════════════════════════════════════════════════════════════════
# build_monetization_doc_scaffold — revenue_map
# ═══════════════════════════════════════════════════════════════════════════════

def test_revenue_map_full_inputs_no_active_stream_gap():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": ["streaming_royalties", "merchandise"],
        "audience_stage": "has_audience",
    }))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "revenue_map"
    keys = [s["key"] for s in res["sections"]]
    assert "active_streams" in keys
    assert "addressable_next" in keys
    assert "diversification_doctrine" in keys
    active_section = next(s for s in res["sections"] if s["key"] == "active_streams")
    assert {r["key"] for r in active_section["recognized"]} == {"streaming_royalties", "merchandise"}
    assert active_section["unknown_streams"] == []
    assert "[ARTIST-SUPPLIED:active_streams]" not in res["missing"]
    assert "[ARTIST-SUPPLIED:audience_stage]" not in res["missing"]


def test_revenue_map_addressable_next_excludes_active_streams():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": ["streaming_royalties"],
        "audience_stage": "has_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "addressable_next")
    candidate_keys = {c["key"] for c in section["candidates"]}
    assert "streaming_royalties" not in candidate_keys
    assert len(section["candidates"]) == len(md.REVENUE_STREAM_TAXONOMY) - 1


def test_revenue_map_missing_active_streams_is_artist_supplied_marker():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {"audience_stage": "has_audience"}))
    assert "[ARTIST-SUPPLIED:active_streams]" in res["missing"]
    active_section = next(s for s in res["sections"] if s["key"] == "active_streams")
    assert active_section["declared"] == []
    assert active_section["recognized"] == []


def test_revenue_map_explicit_empty_active_streams_is_not_a_gap():
    # An explicit [] is a legitimate answer (no streams active yet), not missing.
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [], "audience_stage": "pre_audience",
    }))
    assert "[ARTIST-SUPPLIED:active_streams]" not in res["missing"]
    active_section = next(s for s in res["sections"] if s["key"] == "active_streams")
    assert active_section["declared"] == []


def test_revenue_map_unknown_active_stream_is_noted_not_silently_accepted():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": ["streaming_royalties", "made_up_stream"],
        "audience_stage": "has_audience",
    }))
    active_section = next(s for s in res["sections"] if s["key"] == "active_streams")
    assert active_section["unknown_streams"] == ["made_up_stream"]
    assert {r["key"] for r in active_section["recognized"]} == {"streaming_royalties"}
    unknown_note = next(n for n in res["notes"]
                         if n.get("error") == "unknown_stream")
    assert "made_up_stream" in unknown_note["note"]


def test_revenue_map_missing_audience_stage_is_gap_marker_and_no_filtering_claim():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [],
    }))
    assert "[ARTIST-SUPPLIED:audience_stage]" in res["missing"]
    section = next(s for s in res["sections"] if s["key"] == "addressable_next")
    assert section["stage_filtering_applied"] is False
    # audience-dependent streams cannot be asserted either way when stage is unknown.
    dependent = {c["key"]: c for c in section["candidates"]
                 if c["sequencing_classification"] == "audience_dependent"}
    assert set(dependent) == {"merchandise", "direct_fan_support", "streaming_royalties"}
    for c in dependent.values():
        assert c["addressable"] is None


def test_revenue_map_unrecognized_audience_stage_never_silently_defaulted():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [], "audience_stage": "somewhere_in_between",
    }))
    assert "[ARTIST-SUPPLIED:audience_stage]" not in res["missing"]  # supplied, just unrecognized
    note = next(n for n in res["notes"] if n.get("error") == "unknown_audience_stage")
    assert "somewhere_in_between" in note["note"]
    section = next(s for s in res["sections"] if s["key"] == "addressable_next")
    assert section["stage_filtering_applied"] is False


def test_revenue_map_audience_independent_stream_always_addressable_both_stages():
    for stage in ("pre_audience", "has_audience"):
        res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
            "active_streams": [], "audience_stage": stage,
        }))
        section = next(s for s in res["sections"] if s["key"] == "addressable_next")
        teaching = next(c for c in section["candidates"] if c["key"] == "teaching_and_session_work")
        assert teaching["sequencing_classification"] == "audience_independent"
        assert teaching["addressable"] is True


def test_revenue_map_audience_dependent_streams_gated_by_stage():
    res_pre = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [], "audience_stage": "pre_audience",
    }))
    section_pre = next(s for s in res_pre["sections"] if s["key"] == "addressable_next")
    dependent_pre = {c["key"]: c["addressable"] for c in section_pre["candidates"]
                     if c["sequencing_classification"] == "audience_dependent"}
    assert dependent_pre == {"merchandise": False, "direct_fan_support": False,
                              "streaming_royalties": False}

    res_has = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [], "audience_stage": "has_audience",
    }))
    section_has = next(s for s in res_has["sections"] if s["key"] == "addressable_next")
    dependent_has = {c["key"]: c["addressable"] for c in section_has["candidates"]
                     if c["sequencing_classification"] == "audience_dependent"}
    assert dependent_has == {"merchandise": True, "direct_fan_support": True,
                              "streaming_royalties": True}


def test_revenue_map_unclassified_streams_have_no_known_restriction():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [], "audience_stage": "pre_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "addressable_next")
    unclassified = {c["key"]: c["addressable"] for c in section["candidates"]
                    if c["sequencing_classification"] == "unclassified"}
    assert unclassified == {
        "live_performance": True, "sync_licensing": True, "publishing_royalties": True,
        "content_monetization": True, "brand_partnerships": True, "grants": True,
    }


def test_revenue_map_candidates_carry_prerequisites_and_owning_department_verbatim():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [], "audience_stage": "has_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "addressable_next")
    live = next(c for c in section["candidates"] if c["key"] == "live_performance")
    assert live["prerequisites"] == md.REVENUE_STREAM_TAXONOMY["live_performance"]["prerequisites"]
    assert live["owning_department"] == md.REVENUE_STREAM_TAXONOMY["live_performance"]["owning_department"]


def test_revenue_map_diversification_doctrine_verbatim():
    res = _run(svc.build_monetization_doc_scaffold("revenue_map", {
        "active_streams": [], "audience_stage": "has_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "diversification_doctrine")
    assert section["compounding_relationships"] == md.DIVERSIFICATION["compounding_relationships"]["description"]
    assert section["no_catastrophic_single_point"] == md.DIVERSIFICATION["no_catastrophic_single_point"]["description"]


# ═══════════════════════════════════════════════════════════════════════════════
# build_monetization_doc_scaffold — diversification_plan
# ═══════════════════════════════════════════════════════════════════════════════

def test_diversification_plan_surfaces_two_to_three_candidates():
    res = _run(svc.build_monetization_doc_scaffold("diversification_plan", {
        "active_streams": [], "audience_stage": "has_audience",
    }))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "diversification_plan"
    section = next(s for s in res["sections"] if s["key"] == "next_stream_candidates")
    assert 2 <= len(section["candidates"]) <= 3
    for c in section["candidates"]:
        assert c["addressable"] is True
        assert "prerequisites" in c
        assert "owning_department" in c


def test_diversification_plan_pre_audience_excludes_audience_dependent_candidates():
    res = _run(svc.build_monetization_doc_scaffold("diversification_plan", {
        "active_streams": [], "audience_stage": "pre_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "next_stream_candidates")
    candidate_keys = {c["key"] for c in section["candidates"]}
    assert candidate_keys.isdisjoint({"merchandise", "direct_fan_support", "streaming_royalties"})


def test_diversification_plan_has_audience_can_surface_audience_dependent_candidates():
    res = _run(svc.build_monetization_doc_scaffold("diversification_plan", {
        "active_streams": [], "audience_stage": "has_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "next_stream_candidates")
    candidate_keys = [c["key"] for c in section["candidates"]]
    # Taxonomy order puts streaming_royalties first; with has_audience it is
    # now addressable and should appear among the top candidates.
    assert "streaming_royalties" in candidate_keys


def test_diversification_plan_excludes_already_active_streams():
    res = _run(svc.build_monetization_doc_scaffold("diversification_plan", {
        "active_streams": ["live_performance", "sync_licensing", "publishing_royalties"],
        "audience_stage": "pre_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "next_stream_candidates")
    candidate_keys = {c["key"] for c in section["candidates"]}
    assert candidate_keys.isdisjoint({"live_performance", "sync_licensing", "publishing_royalties"})


def test_diversification_plan_start_small_then_add_doctrine_verbatim():
    res = _run(svc.build_monetization_doc_scaffold("diversification_plan", {
        "active_streams": [], "audience_stage": "has_audience",
    }))
    section = next(s for s in res["sections"] if s["key"] == "start_small_then_add_doctrine")
    assert section["doctrine"] == md.DIVERSIFICATION["start_small_then_add"]["description"]


def test_diversification_plan_missing_active_streams_and_stage_are_gap_markers():
    res = _run(svc.build_monetization_doc_scaffold("diversification_plan", {}))
    assert "[ARTIST-SUPPLIED:active_streams]" in res["missing"]
    assert "[ARTIST-SUPPLIED:audience_stage]" in res["missing"]


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-doc-type invariants
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_doc_type_returns_structured_error():
    res = _run(svc.build_monetization_doc_scaffold("mystery_doc", {}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(svc.DOC_TYPES)


def test_gap_markers_aggregate_and_dedup_across_both_doc_types():
    for doc_type in svc.DOC_TYPES:
        res = _run(svc.build_monetization_doc_scaffold(doc_type, {}))
        assert res["status"] == "scaffold_ready"
        assert isinstance(res["missing"], list)
        assert len(res["missing"]) == len(set(res["missing"])), "missing[] must be deduped"


def test_service_layer_is_entity_wall_clean():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════════════
# THE MOST IMPORTANT TEST IN THIS UNIT: no computed income figure, ever, under
# any input combination, in either doc type.
# ═══════════════════════════════════════════════════════════════════════════════

_INCOME_FIGURE_KEY_RE = re.compile(
    r'"[a-z_]*(total|net_income|gross_income|projected|estimate[d]?|'
    r'income_figure|amount|revenue_total|sum)[a-z_]*"\s*:\s*-?\d')

_INPUT_COMBINATIONS = [
    {},
    {"active_streams": [], "audience_stage": "pre_audience"},
    {"active_streams": [], "audience_stage": "has_audience"},
    {"active_streams": ["streaming_royalties"], "audience_stage": "has_audience"},
    {"active_streams": ["teaching_and_session_work"], "audience_stage": "pre_audience"},
    {"active_streams": ["merchandise", "grants", "brand_partnerships"], "audience_stage": "has_audience"},
    {"active_streams": ["not_a_real_stream"], "audience_stage": "unrecognized_stage"},
    {"active_streams": list(md.REVENUE_STREAM_TAXONOMY), "audience_stage": "has_audience"},
]


def test_neither_scaffold_ever_contains_a_computed_income_figure():
    for doc_type in svc.DOC_TYPES:
        for inputs in _INPUT_COMBINATIONS:
            res = _run(svc.build_monetization_doc_scaffold(doc_type, inputs))
            assert res["status"] == "scaffold_ready"
            blob = json.dumps(res).lower()
            assert not _INCOME_FIGURE_KEY_RE.search(blob), (
                f"computed income figure leaked for doc_type={doc_type} inputs={inputs}")
            for banned_key in ('"total"', '"gross"', '"net"', '"sum"', '"projected_income"',
                               '"estimated_income"', '"income_estimate"', '"average_income"'):
                assert banned_key not in blob, (
                    f"banned key {banned_key} leaked for doc_type={doc_type} inputs={inputs}")
            assert not re.search(r"\$\s*\d", blob), f"currency figure leaked for {doc_type}/{inputs}"


def test_neither_scaffold_header_ever_omits_no_income_projections_doctrine():
    for doc_type in svc.DOC_TYPES:
        res = _run(svc.build_monetization_doc_scaffold(doc_type, {}))
        assert res["header"]["no_income_projections"] == md.MO_DOCTRINE["no_income_projections"]
        assert res["header"]["mechanisms_not_figures"] == md.MO_DOCTRINE["mechanisms_not_figures"]
        assert res["header"]["diversify_dont_concentrate"] == md.MO_DOCTRINE["diversify_dont_concentrate"]


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

def test_mo_tool_roster_is_exactly_the_two_docwriter_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.MOBILE_MONETIZE_TOOLS]
    assert names == ["lookup_monetization_doctrine", "build_monetization_doc_scaffold"]


def test_lookup_tool_enums_match_the_corpus(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    lookup = next(t for t in m.MOBILE_MONETIZE_TOOLS if t["name"] == "lookup_monetization_doctrine")
    props = lookup["input_schema"]["properties"]
    assert props["stream_key"]["enum"] == list(md.REVENUE_STREAM_TAXONOMY)
    assert props["diversification_key"]["enum"] == list(md.DIVERSIFICATION)
    assert props["sequencing_key"]["enum"] == list(md.SEQUENCING)
    assert props["admin_key"]["enum"] == list(md.ADMIN)
    assert "required" not in lookup["input_schema"]  # all filters optional


def test_build_tool_requires_doc_type_with_docwriter_enum(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    build = next(t for t in m.MOBILE_MONETIZE_TOOLS if t["name"] == "build_monetization_doc_scaffold")
    assert build["input_schema"]["required"] == ["doc_type"]
    assert build["input_schema"]["properties"]["doc_type"]["enum"] == list(svc.DOC_TYPES)


def test_dispatch_not_gated_and_returns_three_tuple(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("MOBILE_MONETIZE_CONNECTED", raising=False)
    result, summary, nc = _run(m._execute_mobile_monetize_tool(
        "build_monetization_doc_scaffold",
        {"doc_type": "revenue_map", "inputs": {"active_streams": [], "audience_stage": "has_audience"}},
        "artist-1"))
    assert result["status"] == "scaffold_ready"
    assert nc is False  # gate retired — always False
    assert "section(s) ready" in summary["result"]


def test_dispatch_unknown_tool_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, nc = _run(m._execute_mobile_monetize_tool("nonexistent_tool", {}, "a"))
    assert result["error"] == "unknown_tool"
    assert nc is False


def test_service_roster_is_exactly_the_two_docwriter_functions():
    # This unit's service module exposes exactly the two DOC-WRITER entry
    # points and nothing else callable from the old mock+gate surface — the
    # roster/tool-count tests above already own the exact MOBILE_MONETIZE_TOOLS
    # contents, and the entity-wall + AST checks above cover the rest.
    public_callables = {
        n for n in dir(svc)
        if not n.startswith("_") and callable(getattr(svc, n)) and n != "monetization_data"
    }
    assert public_callables == {"lookup_monetization_doctrine", "build_monetization_doc_scaffold"}
