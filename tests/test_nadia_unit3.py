"""
PROOF tests — Nadia Unit 3: build_royalty_doc_scaffold (doc scaffold writer).

Jade-U4 / Reed-U3 pattern (option B): the tool is DATA-only — compact
ingredients, no model call, no prose. Tests assert structure, section order,
and gap markers; generated prose is NEVER asserted (only the scripted fake
final-text substring in the wiring test). registration_checklist_doc reuses
the Unit-2 checklist engine (situation flags explicit-only — a missing flag is
a surfaced gap and its branch does NOT fire) including the LOD step when
applicable. letter_of_direction consumes LOD_SPEC as data: every field is a
supplied input verbatim, [NEEDS:<field>], or [ARTIST-SUPPLIED: ...];
percentage_directed is NEVER computed or suggested — absent means
[NEEDS:percentage_directed] (REQUIRED no-fabrication invariant). Unknown
doc_type -> structured error. Wiring: dispatch through Nadia's execute path in
the real /api/chat_stream loop, NOT portal-gated; the newest unit owns the
exact tool roster (Reed Unit-3 precedent).
"""
import asyncio
import importlib
import json
import pathlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import ledger_lock_service as svc
import royalties_data
from entity_wall_terms import assert_no_forbidden_terms


class _Block:
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type  = type
        self.text  = text
        self.name  = name
        self.input = input
        self.id    = id


class _Resp:
    def __init__(self, content, stop_reason):
        self.content     = content
        self.stop_reason = stop_reason


def _load_main(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY",      "sk-ant-test")
    monkeypatch.setenv("BANK_CONSULT_MOCK_MODE", "true")
    monkeypatch.setenv("DB_PATH",                str(tmp_path / "test.db"))
    monkeypatch.setenv("DATABASE_URL",           "")
    monkeypatch.setenv("AUDIO_CACHE_DIR",        str(tmp_path / "audio_cache"))
    monkeypatch.setenv("ARTISTS_DIR",            str(tmp_path / "artists"))
    monkeypatch.setenv("ELEVENLABS_API_KEY",     "")
    with patch("whisper.load_model", return_value=MagicMock()):
        # Same re-bake as test_reed_unit2: earlier r-test files leave '/data'
        # baked into the DB_PATH-caching service modules, crashing main reload.
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


def _run(coro):
    return asyncio.run(coro)


_FULL_US_SITUATION = {
    "country_of_residence": "US",
    "self_published": True,
    "owns_masters": True,
    "performed_on_recording": True,
    "has_producers_or_session_players": True,
}

_FULL_LOD_INPUTS = {
    "artist_legal_name": "Ana Reyes",
    "payee_legal_name": "Jo Vega",
    "payee_contact": "jo.vega@mail.test",
    "recordings_covered": "Northern Line (ISRC AA-AAA-26-00001)",
    "percentage_directed": "3% of featured-artist statutory receipts",
    "effective_date": "2026-08-01",
    "signatures_both_parties": "signature lines for Ana Reyes and Jo Vega",
}

_EXPECTED_LOD_ORDER = ["artist_legal_name", "payee_legal_name", "payee_contact",
                       "recordings_covered", "percentage_directed",
                       "effective_date", "signatures_both_parties"]


# ── letter_of_direction branch ─────────────────────────────────────────────────

def test_lod_full_inputs_ordered_sections_no_needs():
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="letter_of_direction", inputs=dict(_FULL_LOD_INPUTS)))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "letter_of_direction"
    assert [s["key"] for s in res["sections"]] == _EXPECTED_LOD_ORDER
    assert res["missing"] == []
    assert res["artist_supplied_reminders"] == []
    # every field is the supplied input VERBATIM — no content is a gap marker
    by_key = {s["key"]: s for s in res["sections"]}
    for field, value in _FULL_LOD_INPUTS.items():
        assert by_key[field]["content_or_gap"] == value
    assert not any(str(s["content_or_gap"]).startswith("[NEEDS:")
                   for s in res["sections"])


def test_lod_missing_percentage_needs_gap_and_never_suggested():
    # REQUIRED no-fabrication invariant: percentage_directed absent -> explicit
    # [NEEDS:percentage_directed], and NO value is computed or suggested
    # anywhere in the result.
    inputs = dict(_FULL_LOD_INPUTS)
    del inputs["percentage_directed"]
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="letter_of_direction", inputs=inputs))
    assert "[NEEDS:percentage_directed]" in res["missing"]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["percentage_directed"]["content_or_gap"] == "[NEEDS:percentage_directed]"

    # no numeric value anywhere — nothing that could read as a suggested %
    def _numeric_leaves(value):
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            found.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                _numeric_leaves(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                _numeric_leaves(v)

    found = []
    _numeric_leaves(res)
    assert found == [], f"a value must never be suggested for a missing %: {found}"
    # the never-computed reminder still rides along
    assert any(r["id"] == "percentage_directed_supplied_only" for r in res["reminders"])


def test_lod_missing_signatures_is_artist_supplied_not_needs():
    inputs = dict(_FULL_LOD_INPUTS)
    del inputs["signatures_both_parties"]
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="letter_of_direction", inputs=inputs))
    by_key = {s["key"]: s for s in res["sections"]}
    content = by_key["signatures_both_parties"]["content_or_gap"]
    assert content.startswith("[ARTIST-SUPPLIED:")
    assert content in res["artist_supplied_reminders"]
    assert not any("signatures_both_parties" in n for n in res["missing"])


def test_lod_missing_other_fields_all_gaps():
    res = _run(svc.build_royalty_doc_scaffold(doc_type="letter_of_direction",
                                              inputs={}))
    for field in _EXPECTED_LOD_ORDER[:-1]:  # all but signatures
        assert f"[NEEDS:{field}]" in res["missing"]
    assert len(res["missing"]) == 6
    assert len(res["artist_supplied_reminders"]) == 1


def test_lod_unmapped_inputs_ride_along_verbatim():
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="letter_of_direction",
        inputs=dict(_FULL_LOD_INPUTS, studio_notes="tracked at Pinewood Room B")))
    assert res["unmapped_inputs"] == {"studio_notes": "tracked at Pinewood Room B"}


# ── registration_checklist_doc branch ──────────────────────────────────────────

def test_checklist_doc_both_hats_us_sections_match_unit2():
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="registration_checklist_doc",
        inputs={"situation": dict(_FULL_US_SITUATION)}))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "registration_checklist_doc"
    assert [s["key"] for s in res["sections"]] == [
        "situation_summary", "registration_steps", "metadata_consistency",
        "letter_of_direction", "reminders"]
    assert res["missing"] == []
    by_key = {s["key"]: s for s in res["sections"]}

    # situation summary carries the supplied flags VERBATIM
    assert by_key["situation_summary"]["content_or_gap"] == _FULL_US_SITUATION

    # steps mirror the Unit-2 checklist exactly (reused, not duplicated)
    checklist = _run(svc.build_registration_checklist(dict(_FULL_US_SITUATION)))
    steps = by_key["registration_steps"]["content_or_gap"]
    assert [s["step"] for s in steps] == list(range(1, len(checklist["registrations"]) + 1))
    assert [s["registration"] for s in steps] == \
        [e["registration"] for e in checklist["registrations"]]
    assert [s["capacity"] for s in steps] == \
        [e["capacity"] for e in checklist["registrations"]]
    # both SoundExchange capacities appear as separate steps
    sx_caps = {s["capacity"] for s in steps
               if s["bodies"] and s["bodies"][0]["id"] == "soundexchange"
               and s["stream_id"] == "us_digital_recording_performance"}
    assert {"rights_owner", "performer"} <= sx_caps

    # metadata block is the corpus doctrine
    assert by_key["metadata_consistency"]["content_or_gap"] == \
        dict(royalties_data.METADATA_DOCTRINE)

    # the LOD step is present (producer flag confirmed) and points at the
    # canonical fields — percentage is supplied-only
    lod = by_key["letter_of_direction"]["content_or_gap"]
    assert lod["canonical_fields"] == [f["field"] for f in royalties_data.LOD_SPEC["fields"]]
    assert "never computed or suggested" in by_key["letter_of_direction"]["guidance"]


def test_checklist_doc_no_producer_flag_false_omits_lod_section():
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="registration_checklist_doc",
        inputs={"situation": dict(_FULL_US_SITUATION,
                                  has_producers_or_session_players=False)}))
    assert "letter_of_direction" not in [s["key"] for s in res["sections"]]
    assert res["missing"] == []


def test_checklist_doc_missing_flag_gap_surfaced_branch_not_defaulted():
    # REQUIRED: an unsupplied axis surfaces as a gap in the summary AND in
    # missing[], and its registration step does NOT appear.
    situation = dict(_FULL_US_SITUATION)
    del situation["owns_masters"]
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="registration_checklist_doc", inputs={"situation": situation}))
    assert "[NEEDS:owns_masters]" in res["missing"]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["situation_summary"]["content_or_gap"]["owns_masters"] == \
        "[NEEDS:owns_masters]"
    steps = by_key["registration_steps"]["content_or_gap"]
    assert "recording_body_rights_owner_registration" not in \
        [s["registration"] for s in steps], "an unsupplied flag must never fire its branch"


def test_checklist_doc_empty_situation_all_gaps_no_steps():
    res = _run(svc.build_royalty_doc_scaffold(
        doc_type="registration_checklist_doc", inputs={}))
    assert len(res["missing"]) == len(royalties_data.REGISTRATION_SITUATION_SPEC)
    by_key = {s["key"]: s for s in res["sections"]}
    assert isinstance(by_key["registration_steps"]["content_or_gap"], str)
    assert by_key["registration_steps"]["content_or_gap"].startswith("[NEEDS:")


# ── shared behavior ────────────────────────────────────────────────────────────

def test_unknown_doc_type_structured_error():
    res = _run(svc.build_royalty_doc_scaffold(doc_type="tax_return", inputs={}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == ["registration_checklist_doc",
                                          "letter_of_direction"]
    assert "sections" not in res


def test_reminders_present_in_both_branches():
    checklist_doc = _run(svc.build_royalty_doc_scaffold(
        doc_type="registration_checklist_doc",
        inputs={"situation": dict(_FULL_US_SITUATION)}))
    lod = _run(svc.build_royalty_doc_scaffold(
        doc_type="letter_of_direction", inputs=dict(_FULL_LOD_INPUTS)))
    for res in (checklist_doc, lod):
        assert "NOT submit-ready" in res["note"]
        assert "NOT tax or legal advice" in res["note"]
        assert "Lex" in res["note"]
    # branch-specific corpus reminders
    reminders_section = next(s for s in checklist_doc["sections"]
                             if s["key"] == "reminders")
    assert "no_tax_or_legal_advice" in reminders_section["content_or_gap"]
    assert [r["id"] for r in lod["reminders"]] == \
        [r["id"] for r in royalties_data.LOD_SPEC["reminders"]]


def test_every_scaffold_result_is_json_serializable():
    for res in (
        _run(svc.build_royalty_doc_scaffold(doc_type="registration_checklist_doc",
                                            inputs={})),
        _run(svc.build_royalty_doc_scaffold(doc_type="letter_of_direction",
                                            inputs={})),
        _run(svc.build_royalty_doc_scaffold(doc_type="nope", inputs={})),
    ):
        json.dumps(res)


def test_service_source_is_entity_wall_clean_unit3():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


def test_service_imports_no_anthropic_unit3():
    # Option B: zero messages.create in the tool layer, no LLM SDK import.
    import ast as _ast
    source = pathlib.Path(svc.__file__).read_text(encoding="utf-8")
    assert "messages.create" not in source
    tree = _ast.parse(source)
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, _ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "anthropic" not in name.lower()


# ── wiring through the real loop ───────────────────────────────────────────────

def test_wire_scaffold_dispatch_not_portal_gated(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("LEDGER_LOCK_ACCOUNT_CONNECTED", raising=False)

    scaffold_calls = []
    real_scaffold = m.ledger_lock_service.build_royalty_doc_scaffold

    async def rec_scaffold(doc_type="", inputs=None):
        scaffold_calls.append({"doc_type": doc_type})
        return await real_scaffold(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.ledger_lock_service, "build_royalty_doc_scaffold",
                        rec_scaffold)

    responses = [
        _Resp([_Block("tool_use", name="build_royalty_doc_scaffold",
                      input={"doc_type": "letter_of_direction",
                             "inputs": dict(_FULL_LOD_INPUTS)},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is your letter of direction draft to review.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ledger-lock",
        "message":   "draft the letter of direction for my producer",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert scaffold_calls == [{"doc_type": "letter_of_direction"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "build_royalty_doc_scaffold"
    assert "scaffold_ready" in actions_evt["actions_taken"][0]["result"]
    assert "gap(s)" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["ledger_account_not_connected"] is False, \
        "scaffold tool must not trip the gate"
    done_evt = next(e for e in events if e["type"] == "done")
    assert "letter of direction draft" in done_evt["full_text"]  # scripted fake text only
    assert all(kw.get("tools") == m.LEDGER_LOCK_TOOLS for kw in create_calls)


def test_dispatch_unknown_doc_type_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(m._execute_ledger_lock_tool(
        "build_royalty_doc_scaffold", {"doc_type": "tax_return"}, "artist-9"))
    assert res["status"] == "unknown_doc_type"
    assert summary["result"] == "unknown_doc_type"
    assert nc is False


def test_ledger_lock_tools_now_six(monkeypatch, tmp_path):
    # Reed Unit-3 precedent: the newest unit owns the EXACT tool roster.
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.LEDGER_LOCK_TOOLS]
    assert names == ["search_royalty_sources", "reconcile_royalty_statement",
                     "file_tax_document", "lookup_recording_societies",
                     "build_registration_checklist", "build_royalty_doc_scaffold"]
    scaffold = next(t for t in m.LEDGER_LOCK_TOOLS
                    if t["name"] == "build_royalty_doc_scaffold")
    assert scaffold["input_schema"]["required"] == ["doc_type"]
    assert scaffold["input_schema"]["properties"]["doc_type"]["enum"] == \
        ["registration_checklist_doc", "letter_of_direction"]
    # Reed Unit-2 precedent: fabrication-risk sub-fields are described, never forced
    assert "required" not in scaffold["input_schema"]["properties"]["inputs"]
