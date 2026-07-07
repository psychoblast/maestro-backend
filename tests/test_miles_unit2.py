"""
PROOF tests — Miles Unit 2 (DOC-WRITER Option B service + wiring).

Locks the two replacement tools, permanently:

  lookup_tour_ops_doctrine — pure corpus read/filter over tour_ops_data,
    UNGATED (no env, no account); index mode with no filters; per-block
    filtering; a filter that matches nothing lands in not_found with value
    None (never guessed).

  build_tour_doc_scaffold — OPTION B: COMPACT ingredients only, no prose, no
    model call (AST-enforced: the service imports no LLM SDK and contains no
    ``messages.create``). Three doc types:
      * advance_pack — venue-vs-production-advance distinction, package
        checklist, venue-provides fields, union-house risk, parking doctrine;
        deal memo is [ARTIST-SUPPLIED:deal_memo], never invented.
      * day_sheet — HARD PRIVACY RULE: sensitive fields (hotel info, door
        codes, flight details) excluded from the default/printable output;
        only an explicit include_sensitive request on the principal variant
        surfaces them.
      * settlement_prep_sheet — deal terms restated verbatim + prep checklist
        + walk-the-numbers questions; NEVER a computed total.

  This unit OWNS the exact Miles tool roster/count. NEVER asserts generated
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

import tour_ops_data as td
import tour_commander_service as svc
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
        # Same '/data'-rebake guard as test_cree_unit2 / test_nadia_unit3 / test_lex_unit2.
        import booking_service, phase4_service, pitch_service
        import pr_service, release_service, social_service
        for _svc_mod in (booking_service, phase4_service, pitch_service,
                         pr_service, release_service, social_service):
            importlib.reload(_svc_mod)
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
# lookup_tour_ops_doctrine — pure corpus read, ungated
# ═══════════════════════════════════════════════════════════════════════════════

def test_lookup_index_mode_lists_all_block_keys(monkeypatch):
    monkeypatch.delenv("TOUR_COMMANDER_ACCOUNT_CONNECTED", raising=False)  # no gate exists
    res = _run(svc.lookup_tour_ops_doctrine())
    assert res["status"] == "ok"
    assert res["mode"] == "index"
    assert res["advancing_keys"] == list(td.ADVANCING_DOCTRINE)
    assert res["day_sheet_fields"] == [rec["field"] for rec in td.DAY_SHEET_SPEC]
    assert res["settlement_keys"] == list(td.SETTLEMENT_PREP_DOCTRINE)
    assert res["routing_keys"] == list(td.ROUTING_AND_PREP)
    assert res["festival_keys"] == list(td.FESTIVAL_VARIANT)
    assert res["vocabulary_terms"] == list(td.SETTLEMENT_VOCABULARY)
    assert res["day_sheet_variant_keys"] == list(td.DAY_SHEET_VARIANTS)
    assert res["miles_doctrine"] == dict(td.MILES_DOCTRINE)


def test_lookup_filters_each_block_and_returns_full_records():
    res = _run(svc.lookup_tour_ops_doctrine(
        advancing_key="venue_advance", day_sheet_field="artist_hotel_info",
        settlement_key="confirm_the_deposit", routing_key="routing_sheet_fields",
        festival_key="welcome_letter_topics", vocabulary_term="ticket_buys"))
    assert res["mode"] == "filtered"
    assert res["advancing"][0]["key"] == "venue_advance"
    assert res["day_sheet"][0]["field"] == "artist_hotel_info"
    assert res["settlement"][0]["key"] == "confirm_the_deposit"
    assert res["routing"][0]["key"] == "routing_sheet_fields"
    assert res["festival"][0]["key"] == "welcome_letter_topics"
    assert res["vocabulary"][0]["term"] == "ticket_buys"
    assert res["not_found"] == []


def test_lookup_unknown_key_recorded_as_not_found_never_guessed():
    res = _run(svc.lookup_tour_ops_doctrine(settlement_key="no_such_key"))
    assert res["settlement"] == []
    assert res["not_found"] == [{"filter": "settlement_key", "value": "no_such_key", "match": None}]


def test_lookup_always_carries_miles_doctrine_and_boundaries():
    res = _run(svc.lookup_tour_ops_doctrine(advancing_key="venue_advance"))
    boundary_keys = {b["key"] for b in res["boundaries"]}
    assert {"booking_and_deal_terms", "royalty_and_accounting"} <= boundary_keys
    assert "prep_not_negotiation" in res["miles_doctrine"]


# ═══════════════════════════════════════════════════════════════════════════════
# build_tour_doc_scaffold — advance_pack
# ═══════════════════════════════════════════════════════════════════════════════

_FULL_ADVANCE_INPUTS = {
    "deal_memo": "One night, headline, agreed fee structure per contract.",
}


def test_advance_pack_full_inputs_ready_all_sections_no_gaps():
    res = _run(svc.build_tour_doc_scaffold("advance_pack", _FULL_ADVANCE_INPUTS))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "advance_pack"
    keys = [s["key"] for s in res["sections"]]
    assert "venue_vs_production_advance" in keys
    assert "advance_package_checklist" in keys
    assert "venue_provides" in keys
    assert "union_house_risk" in keys
    assert "parking_doctrine" in keys
    assert "deal_memo" in keys
    assert res["missing"] == []


def test_advance_pack_venue_vs_production_distinction_present():
    res = _run(svc.build_tour_doc_scaffold("advance_pack", _FULL_ADVANCE_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "venue_vs_production_advance")
    assert "venue" in section["venue_advance"].lower()
    assert "production" in section["production_advance"].lower()
    assert section["venue_advance"] != section["production_advance"]


def test_advance_pack_deal_memo_missing_is_artist_supplied_marker():
    res = _run(svc.build_tour_doc_scaffold("advance_pack", {}))
    assert "[ARTIST-SUPPLIED:deal_memo]" in res["missing"]
    assert "deal_memo" not in [s["key"] for s in res["sections"]]


def test_advance_pack_deal_memo_rides_verbatim_when_supplied():
    res = _run(svc.build_tour_doc_scaffold("advance_pack", _FULL_ADVANCE_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "deal_memo")
    assert section["content"] == _FULL_ADVANCE_INPUTS["deal_memo"]  # verbatim


def test_advance_pack_boundary_note_routes_to_venue_hawk():
    res = _run(svc.build_tour_doc_scaffold("advance_pack", _FULL_ADVANCE_INPUTS))
    note = next(n for n in res["notes"] if n["section"] == "boundaries")
    assert "venue-hawk" in note["note"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# build_tour_doc_scaffold — day_sheet (HARD PRIVACY RULE)
# ═══════════════════════════════════════════════════════════════════════════════

_DAY_SHEET_INPUTS = {
    "doors": "7:00 PM",
    "curfew": "11:00 PM",
    "artist_hotel_info": "Hotel Regal, room 204",
    "door_codes": "1234#",
    "flight_details": "AA123 arriving 14:20",
}


def test_day_sheet_sensitive_fields_excluded_by_default():
    res = _run(svc.build_tour_doc_scaffold("day_sheet", _DAY_SHEET_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "day_sheet_fields")
    field_names = {f["field"] for f in section["fields"]}
    # sensitive fields ABSENT from the default/printable output
    assert "artist_hotel_info" not in field_names
    assert "door_codes" not in field_names
    assert "flight_details" not in field_names
    # non-sensitive fields ARE present
    assert "doors" in field_names
    assert "curfew" in field_names
    assert section["variant"] == "printable"
    assert set(section["sensitive_fields_excluded"]) == {
        "artist_hotel_info", "door_codes", "flight_details"}


def test_day_sheet_sensitive_fields_included_on_explicit_principal_request():
    inp = dict(_DAY_SHEET_INPUTS)
    inp["variant"] = "principal"
    inp["include_sensitive"] = True
    res = _run(svc.build_tour_doc_scaffold("day_sheet", inp))
    section = next(s for s in res["sections"] if s["key"] == "day_sheet_fields")
    by_field = {f["field"]: f for f in section["fields"]}
    assert by_field["artist_hotel_info"]["value"] == _DAY_SHEET_INPUTS["artist_hotel_info"]
    assert by_field["door_codes"]["value"] == _DAY_SHEET_INPUTS["door_codes"]
    assert by_field["flight_details"]["value"] == _DAY_SHEET_INPUTS["flight_details"]
    assert section["sensitive_fields_excluded"] == []


def test_day_sheet_include_sensitive_ignored_on_default_printable_variant():
    # include_sensitive=True WITHOUT variant="principal" must NOT surface sensitive fields.
    inp = dict(_DAY_SHEET_INPUTS)
    inp["include_sensitive"] = True
    res = _run(svc.build_tour_doc_scaffold("day_sheet", inp))
    section = next(s for s in res["sections"] if s["key"] == "day_sheet_fields")
    field_names = {f["field"] for f in section["fields"]}
    assert "artist_hotel_info" not in field_names
    assert "door_codes" not in field_names
    assert "flight_details" not in field_names


def test_day_sheet_missing_field_values_are_artist_supplied_markers():
    res = _run(svc.build_tour_doc_scaffold("day_sheet", {}))
    assert "[ARTIST-SUPPLIED:doors]" in res["missing"]
    assert "[ARTIST-SUPPLIED:curfew]" in res["missing"]
    # sensitive fields excluded entirely — no gap marker for them at default variant
    assert "[ARTIST-SUPPLIED:artist_hotel_info]" not in res["missing"]


def test_day_sheet_variants_doctrine_present():
    res = _run(svc.build_tour_doc_scaffold("day_sheet", _DAY_SHEET_INPUTS))
    section = next(s for s in res["sections"] if s["key"] == "day_sheet_variants_doctrine")
    assert "principal" in section["doctrine"].lower()
    assert "crew" in section["doctrine"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# build_tour_doc_scaffold — settlement_prep_sheet (NEVER a computed total)
# ═══════════════════════════════════════════════════════════════════════════════

_TOTAL_KEY_RE = re.compile(r'"[a-z_]*(total|net_amount|gross_amount|sum)[a-z_]*"\s*:\s*-?\d')


def test_settlement_prep_sheet_never_contains_a_computed_total():
    scaffolds = [
        _run(svc.build_tour_doc_scaffold("settlement_prep_sheet",
                                         {"deal_terms": "Flat guarantee, net merch split."})),
        _run(svc.build_tour_doc_scaffold("settlement_prep_sheet", {})),
    ]
    for res in scaffolds:
        blob = json.dumps(res).lower()
        assert not _TOTAL_KEY_RE.search(blob), "computed total/sum/gross/net numeric field leaked"
        # No arithmetic result key of any kind.
        for banned_key in ('"total"', '"gross"', '"net"', '"sum"'):
            assert banned_key not in blob


def test_settlement_prep_sheet_deal_terms_restated_verbatim():
    res = _run(svc.build_tour_doc_scaffold(
        "settlement_prep_sheet", {"deal_terms": "Flat guarantee, net merch split."}))
    section = next(s for s in res["sections"] if s["key"] == "deal_terms_restated")
    assert section["content"] == "Flat guarantee, net merch split."
    assert res["missing"] == []


def test_settlement_prep_sheet_deal_terms_missing_is_artist_supplied_marker():
    res = _run(svc.build_tour_doc_scaffold("settlement_prep_sheet", {}))
    assert "[ARTIST-SUPPLIED:deal_terms]" in res["missing"]
    assert "deal_terms_restated" not in [s["key"] for s in res["sections"]]


def test_settlement_prep_sheet_checklist_and_questions_present():
    res = _run(svc.build_tour_doc_scaffold("settlement_prep_sheet", {"deal_terms": "x"}))
    keys = [s["key"] for s in res["sections"]]
    assert "settlement_prep_checklist" in keys
    assert "walk_the_numbers_questions" in keys
    checklist = next(s for s in res["sections"] if s["key"] == "settlement_prep_checklist")
    assert {item["key"] for item in checklist["items"]} == set(td.SETTLEMENT_PREP_DOCTRINE)
    questions = next(s for s in res["sections"] if s["key"] == "walk_the_numbers_questions")
    for q in questions["questions"]:
        assert "?" in q


def test_settlement_prep_sheet_notes_ledger_lock_boundary():
    res = _run(svc.build_tour_doc_scaffold("settlement_prep_sheet", {"deal_terms": "x"}))
    note = next(n for n in res["notes"] if n["section"] == "ledger_lock_boundary")
    assert "ledger-lock" in note["note"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-doc-type invariants
# ═══════════════════════════════════════════════════════════════════════════════

def test_unknown_doc_type_returns_structured_error():
    res = _run(svc.build_tour_doc_scaffold("mystery_doc", {}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(svc.DOC_TYPES)


def test_gap_markers_aggregate_across_all_three_doc_types():
    for doc_type in svc.DOC_TYPES:
        res = _run(svc.build_tour_doc_scaffold(doc_type, {}))
        assert res["status"] == "scaffold_ready"
        assert isinstance(res["missing"], list)
        assert len(res["missing"]) == len(set(res["missing"])), "missing[] must be deduped"


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

def test_miles_tool_roster_is_exactly_the_two_docwriter_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.TOUR_COMMANDER_TOOLS]
    assert names == ["lookup_tour_ops_doctrine", "build_tour_doc_scaffold"]


def test_lookup_tool_enums_match_the_corpus(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    lookup = next(t for t in m.TOUR_COMMANDER_TOOLS if t["name"] == "lookup_tour_ops_doctrine")
    props = lookup["input_schema"]["properties"]
    assert props["advancing_key"]["enum"] == list(td.ADVANCING_DOCTRINE)
    assert props["day_sheet_field"]["enum"] == [rec["field"] for rec in td.DAY_SHEET_SPEC]
    assert props["settlement_key"]["enum"] == list(td.SETTLEMENT_PREP_DOCTRINE)
    assert props["routing_key"]["enum"] == list(td.ROUTING_AND_PREP)
    assert props["festival_key"]["enum"] == list(td.FESTIVAL_VARIANT)
    assert props["vocabulary_term"]["enum"] == list(td.SETTLEMENT_VOCABULARY)
    assert "required" not in lookup["input_schema"]  # all filters optional


def test_build_tool_requires_doc_type_with_docwriter_enum(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    build = next(t for t in m.TOUR_COMMANDER_TOOLS if t["name"] == "build_tour_doc_scaffold")
    assert build["input_schema"]["required"] == ["doc_type"]
    assert build["input_schema"]["properties"]["doc_type"]["enum"] == list(svc.DOC_TYPES)


def test_dispatch_not_gated_and_returns_three_tuple(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("TOUR_COMMANDER_ACCOUNT_CONNECTED", raising=False)
    result, summary, tonc = _run(m._execute_tour_commander_tool(
        "build_tour_doc_scaffold",
        {"doc_type": "advance_pack", "inputs": {"deal_memo": "x"}},
        "artist-1"))
    assert result["status"] == "scaffold_ready"
    assert tonc is False  # gate retired — always False
    assert "section(s)" in summary["result"]


def test_dispatch_unknown_tool_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    result, summary, tonc = _run(m._execute_tour_commander_tool("nonexistent_tool", {}, "a"))
    assert result["error"] == "unknown_tool"
    assert tonc is False


def test_service_roster_is_exactly_the_two_docwriter_functions():
    # This unit's service module exposes exactly the two DOC-WRITER entry
    # points and nothing else callable from the old mock+gate surface — the
    # roster/tool-count tests above already own the exact TOUR_COMMANDER_TOOLS
    # contents, and the entity-wall + AST checks above cover the rest.
    public_callables = {
        n for n in dir(svc)
        if not n.startswith("_") and callable(getattr(svc, n)) and n != "tour_ops_data"
    }
    assert public_callables == {"lookup_tour_ops_doctrine", "build_tour_doc_scaffold"}
