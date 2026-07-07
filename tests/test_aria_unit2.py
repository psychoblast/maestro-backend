"""
PROOF tests — Aria Unit 2 (DOC-WRITER Option B service + wiring).

Locks the two replacement tools, permanently:

  lookup_engagement_doctrine — pure corpus read/filter over engagement_data,
    UNGATED (no env, no account); index mode with no filters; per-block
    filtering; a filter that matches nothing lands in not_found with value
    None (never guessed).

  build_engagement_doc_scaffold — OPTION B: COMPACT ingredients only, no
    prose, no model call (AST-enforced: the service imports no LLM SDK and
    contains no ``messages.create``). Two doc types:
      * engagement_plan — funnel-stage assessment questions, a cadence plan
        (weekly + per-release-cycle restated verbatim from CADENCE_SPEC, plus
        the artist's own current-weekly-focus restatement), and a superfan-
        nurture checklist.
      * superfan_program_outline — FAN_FUNNEL's three tiers restated
        verbatim, plus access-perk ingredients sourced from
        inputs["offerings"]; any perk type Aria's doctrine names that the
        artist did not supply becomes an [ARTIST-SUPPLIED:<perk_type>]
        marker.

  This unit OWNS the exact Aria tool roster/count. NEVER asserts generated
  prose — scaffolds are structured; the Anthropic client is faked in the
  wiring tests. A dedicated test also locks the never_simulates_sending
  invariant as a real, tested behavior — not just a doctrine comment.
"""
import ast
import asyncio
import importlib
import json
import pathlib
import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import engagement_data as ed
import fan_builder_service as svc
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
# lookup_engagement_doctrine — pure corpus read, ungated
# ═══════════════════════════════════════════════════════════════════════════════

def test_lookup_index_mode_lists_all_block_keys(monkeypatch):
    monkeypatch.delenv("FAN_BUILDER_ACCOUNT_CONNECTED", raising=False)  # no gate exists
    res = _run(svc.lookup_engagement_doctrine())
    assert res["status"] == "ok"
    assert res["mode"] == "index"
    assert res["funnel_keys"] == list(ed.FAN_FUNNEL)
    assert res["principle_keys"] == list(ed.THOUSAND_TRUE_FANS)
    assert res["signal_keys"] == list(ed.SUPERFAN_IDENTIFICATION)
    assert res["channel_keys"] == list(ed.OWNED_CHANNELS)
    assert res["cadence_keys"] == list(ed.CADENCE_SPEC)
    assert res["waste_keys"] == list(ed.WHAT_WASTES_TIME)
    assert res["aria_doctrine"] == dict(ed.ARIA_DOCTRINE)


def test_lookup_filters_each_block_and_returns_full_records():
    res = _run(svc.lookup_engagement_doctrine(
        funnel_key="superfan", principle_key="depth_over_scale_principle",
        signal_key="shares_unprompted", channel_key="owned_channels_email_sms",
        cadence_key="weekly_cadence", waste_key="chasing_vanity_metrics"))
    assert res["mode"] == "filtered"
    assert res["funnel"][0]["key"] == "superfan"
    assert res["principles"][0]["key"] == "depth_over_scale_principle"
    assert res["signals"][0]["key"] == "shares_unprompted"
    assert res["channels"][0]["key"] == "owned_channels_email_sms"
    assert res["cadence"][0]["key"] == "weekly_cadence"
    assert res["waste"][0]["key"] == "chasing_vanity_metrics"
    assert res["not_found"] == []


def test_lookup_unknown_key_recorded_as_not_found_never_guessed():
    res = _run(svc.lookup_engagement_doctrine(waste_key="no_such_key"))
    assert res["waste"] == []
    assert res["not_found"] == [{"filter": "waste_key", "value": "no_such_key", "match": None}]


def test_lookup_always_carries_aria_doctrine_and_boundaries():
    res = _run(svc.lookup_engagement_doctrine(funnel_key="superfan"))
    boundary_keys = {b["key"] for b in res["boundaries"]}
    assert {"post_scheduling_and_execution", "monetizing_the_fanbase",
            "email_sms_sending_infrastructure"} <= boundary_keys
    assert "depth_over_scale" in res["aria_doctrine"]


# ═══════════════════════════════════════════════════════════════════════════════
# build_engagement_doc_scaffold — engagement_plan
# ═══════════════════════════════════════════════════════════════════════════════

_FULL_ENGAGEMENT_PLAN_INPUTS = {
    "current_weekly_focus": "Replying to comments on the last single's posts.",
}


def test_engagement_plan_full_inputs_ready_all_sections_no_gaps():
    res = _run(svc.build_engagement_doc_scaffold("engagement_plan", _FULL_ENGAGEMENT_PLAN_INPUTS))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "engagement_plan"
    keys = [s["key"] for s in res["sections"]]
    assert "funnel_stage_assessment_questions" in keys
    assert "cadence_plan" in keys
    assert "superfan_nurture_checklist" in keys
    assert res["missing"] == []


def test_engagement_plan_assessment_questions_present_and_are_questions():
    res = _run(svc.build_engagement_doc_scaffold("engagement_plan", _FULL_ENGAGEMENT_PLAN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "funnel_stage_assessment_questions")
    assert len(section["questions"]) >= 3
    for q in section["questions"]:
        assert "?" in q


def test_engagement_plan_cadence_restated_verbatim_from_corpus():
    res = _run(svc.build_engagement_doc_scaffold("engagement_plan", _FULL_ENGAGEMENT_PLAN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "cadence_plan")
    assert section["weekly_cadence"] == dict(ed.CADENCE_SPEC["weekly_cadence"])
    assert section["per_release_cycle_cadence"] == dict(ed.CADENCE_SPEC["per_release_cycle_cadence"])


def test_engagement_plan_current_weekly_focus_missing_is_artist_supplied_marker():
    res = _run(svc.build_engagement_doc_scaffold("engagement_plan", {}))
    assert "[ARTIST-SUPPLIED:current_weekly_focus]" in res["missing"]
    section = next(s for s in res["sections"] if s["key"] == "cadence_plan")
    assert section["current_weekly_focus"] == "[ARTIST-SUPPLIED:current_weekly_focus]"


def test_engagement_plan_current_weekly_focus_rides_verbatim_when_supplied():
    res = _run(svc.build_engagement_doc_scaffold("engagement_plan", _FULL_ENGAGEMENT_PLAN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "cadence_plan")
    assert section["current_weekly_focus"] == _FULL_ENGAGEMENT_PLAN_INPUTS["current_weekly_focus"]


def test_engagement_plan_superfan_nurture_checklist_sources_the_right_practices():
    res = _run(svc.build_engagement_doc_scaffold("engagement_plan", _FULL_ENGAGEMENT_PLAN_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "superfan_nurture_checklist")
    item_keys = {item["key"] for item in section["items"]}
    assert item_keys == {"track_and_recognize_practice", "private_small_group_access_nurture_pattern"}


# ═══════════════════════════════════════════════════════════════════════════════
# build_engagement_doc_scaffold — superfan_program_outline
# ═══════════════════════════════════════════════════════════════════════════════

_FULL_SUPERFAN_PROGRAM_INPUTS = {
    "offerings": {
        "early_listens": "48-hour early access link before public release.",
        "decision_votes": "A poll on the next single's cover art.",
        "beta_merch": "First look at the new hoodie design before the store opens.",
    },
}


def test_superfan_program_outline_full_inputs_ready_all_sections_no_gaps():
    res = _run(svc.build_engagement_doc_scaffold(
        "superfan_program_outline", _FULL_SUPERFAN_PROGRAM_INPUTS))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "superfan_program_outline"
    keys = [s["key"] for s in res["sections"]]
    assert "tier_structure" in keys
    assert "access_perks" in keys
    assert res["missing"] == []


def test_superfan_program_outline_tier_structure_is_the_three_fan_funnel_tiers_verbatim():
    res = _run(svc.build_engagement_doc_scaffold(
        "superfan_program_outline", _FULL_SUPERFAN_PROGRAM_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "tier_structure")
    tier_keys = [t["key"] for t in section["tiers"]]
    assert tier_keys == ["casual", "true_fan", "superfan"]
    for t in section["tiers"]:
        assert t == dict(ed.FAN_FUNNEL[t["key"]])


def test_superfan_program_outline_perks_ride_verbatim_when_supplied():
    res = _run(svc.build_engagement_doc_scaffold(
        "superfan_program_outline", _FULL_SUPERFAN_PROGRAM_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "access_perks")
    by_type = {p["perk_type"]: p["value"] for p in section["perks"]}
    assert by_type["early_listens"] == _FULL_SUPERFAN_PROGRAM_INPUTS["offerings"]["early_listens"]
    assert by_type["decision_votes"] == _FULL_SUPERFAN_PROGRAM_INPUTS["offerings"]["decision_votes"]
    assert by_type["beta_merch"] == _FULL_SUPERFAN_PROGRAM_INPUTS["offerings"]["beta_merch"]


def test_superfan_program_outline_missing_perks_become_artist_supplied_markers():
    res = _run(svc.build_engagement_doc_scaffold(
        "superfan_program_outline", {"offerings": {"early_listens": "48h early link."}}))
    assert "[ARTIST-SUPPLIED:decision_votes]" in res["missing"]
    assert "[ARTIST-SUPPLIED:beta_merch]" in res["missing"]
    assert "[ARTIST-SUPPLIED:early_listens]" not in res["missing"]
    section = next(s for s in res["sections"] if s["key"] == "access_perks")
    by_type = {p["perk_type"]: p["value"] for p in section["perks"]}
    assert by_type["decision_votes"] == "[ARTIST-SUPPLIED:decision_votes]"
    assert by_type["beta_merch"] == "[ARTIST-SUPPLIED:beta_merch]"


def test_superfan_program_outline_no_offerings_all_three_perks_are_gaps():
    res = _run(svc.build_engagement_doc_scaffold("superfan_program_outline", {}))
    assert "[ARTIST-SUPPLIED:early_listens]" in res["missing"]
    assert "[ARTIST-SUPPLIED:decision_votes]" in res["missing"]
    assert "[ARTIST-SUPPLIED:beta_merch]" in res["missing"]


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-doc-type invariants
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_doc_type_returns_structured_error():
    res = _run(svc.build_engagement_doc_scaffold("mystery_doc", {}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(svc.DOC_TYPES)


def test_gap_markers_aggregate_across_both_doc_types():
    for doc_type in svc.DOC_TYPES:
        res = _run(svc.build_engagement_doc_scaffold(doc_type, {}))
        assert res["status"] == "scaffold_ready"
        assert isinstance(res["missing"], list)
        assert len(res["missing"]) == len(set(res["missing"])), "missing[] must be deduped"


def test_header_carries_aria_doctrine_on_both_doc_types():
    for doc_type in svc.DOC_TYPES:
        res = _run(svc.build_engagement_doc_scaffold(doc_type, {}))
        header = res["header"]
        assert header["depth_over_scale"] == ed.ARIA_DOCTRINE["depth_over_scale"]
        assert header["superfans_first"] == ed.ARIA_DOCTRINE["superfans_first"]
        assert header["owned_over_rented"] == ed.ARIA_DOCTRINE["owned_over_rented"]
        assert header["never_simulates_sending"] == ed.ARIA_DOCTRINE["never_simulates_sending"]


def test_service_layer_is_entity_wall_clean():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════════════════
# never_simulates_sending — a real, tested invariant, not just a comment
# ═══════════════════════════════════════════════════════════════════════════════

_SEND_CONFIRMATION_PHRASES = (
    "message sent", "message has been sent", "email sent", "sms sent",
    "broadcast sent", "broadcast scheduled", "has gone out", "was delivered",
    "delivery confirmed", "sent to fans", "sent successfully",
)


def test_scaffolds_never_claim_a_message_was_sent():
    scaffolds = [
        _run(svc.build_engagement_doc_scaffold("engagement_plan", _FULL_ENGAGEMENT_PLAN_INPUTS)),
        _run(svc.build_engagement_doc_scaffold("engagement_plan", {})),
        _run(svc.build_engagement_doc_scaffold("superfan_program_outline", _FULL_SUPERFAN_PROGRAM_INPUTS)),
        _run(svc.build_engagement_doc_scaffold("superfan_program_outline", {})),
    ]
    for res in scaffolds:
        blob = json.dumps(res).lower()
        for phrase in _SEND_CONFIRMATION_PHRASES:
            assert phrase not in blob, f"'{phrase}' leaked into scaffold output: {blob}"


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

def test_aria_tool_roster_is_exactly_the_two_docwriter_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.FAN_BUILDER_TOOLS]
    assert names == ["lookup_engagement_doctrine", "build_engagement_doc_scaffold"]


def test_lookup_tool_enums_match_the_corpus(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    lookup = next(t for t in m.FAN_BUILDER_TOOLS if t["name"] == "lookup_engagement_doctrine")
    props = lookup["input_schema"]["properties"]
    assert props["funnel_key"]["enum"] == list(ed.FAN_FUNNEL)
    assert props["principle_key"]["enum"] == list(ed.THOUSAND_TRUE_FANS)
    assert props["signal_key"]["enum"] == list(ed.SUPERFAN_IDENTIFICATION)
    assert props["channel_key"]["enum"] == list(ed.OWNED_CHANNELS)
    assert props["cadence_key"]["enum"] == list(ed.CADENCE_SPEC)
    assert props["waste_key"]["enum"] == list(ed.WHAT_WASTES_TIME)
    assert "required" not in lookup["input_schema"]  # all filters optional


def test_build_tool_requires_doc_type_with_docwriter_enum(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    build = next(t for t in m.FAN_BUILDER_TOOLS if t["name"] == "build_engagement_doc_scaffold")
    assert build["input_schema"]["required"] == ["doc_type"]
    assert build["input_schema"]["properties"]["doc_type"]["enum"] == list(svc.DOC_TYPES)


def test_dispatch_not_gated_and_returns_three_tuple(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("FAN_BUILDER_ACCOUNT_CONNECTED", raising=False)
    result, summary, fnc = _run(m._execute_fan_builder_tool(
        "build_engagement_doc_scaffold",
        {"doc_type": "engagement_plan", "inputs": {"current_weekly_focus": "x"}},
        "artist-1"))
    assert result["status"] == "scaffold_ready"
    assert fnc is False  # gate retired — always False
    assert "section(s)" in summary["result"]


def test_dispatch_unknown_tool_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, fnc = _run(m._execute_fan_builder_tool("nonexistent_tool", {}, "a"))
    assert result["error"] == "unknown_tool"
    assert fnc is False


def test_service_roster_is_exactly_the_two_docwriter_functions():
    # This unit's service module exposes exactly the two DOC-WRITER entry
    # points and nothing else callable from the old mock+gate surface — the
    # roster/tool-count tests above already own the exact FAN_BUILDER_TOOLS
    # contents, and the entity-wall + AST checks above cover the rest.
    public_callables = {
        n for n in dir(svc)
        if not n.startswith("_") and callable(getattr(svc, n)) and n != "engagement_data"
    }
    assert public_callables == {"lookup_engagement_doctrine", "build_engagement_doc_scaffold"}
