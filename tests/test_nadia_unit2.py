"""
PROOF tests — Nadia Unit 2: recording-society lookup + registration checklist.

Service layer: lookup_recording_societies is a pure read of the Unit-1 corpus
(royalties_data, with composition-side context ids resolved read-only via
publishing_data) — US digital-only scope with the International Mandate note,
France's four-body role split, NZ's honestly-unverified recording side, and an
honest country_not_in_corpus for anything outside the 11 covered codes.
build_registration_checklist applies REGISTRATION_RULES to EXPLICITLY supplied
situation flags only: an unsupplied axis is a [NEEDS:<flag>] gap and its rule
branch does NOT fire (the no-fabrication invariant test is REQUIRED); no split
is ever stated as fact except the US statutory SoundExchange 50/45/5 —
everything else is varies_verify_with_society. Structure only, never prose.

Wiring: both new tools dispatch through _execute_ledger_lock_tool inside the
real /api/chat_stream loop (scripted _Resp/_Block fakes), and neither is gated
on LEDGER_LOCK_ACCOUNT_CONNECTED. Zero network / LLM.
"""
import asyncio
import importlib
import json
import pathlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import ledger_lock_service as svc
import publishing_data
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


# A both-hats, self-published US artist who worked with a producer — every
# axis explicitly supplied.
_FULL_US_SITUATION = {
    "country_of_residence": "US",
    "self_published": True,
    "owns_masters": True,
    "performed_on_recording": True,
    "has_producers_or_session_players": True,
}


def _assert_no_non_statutory_split(result: dict):
    """REQUIRED discipline: the only numbers that look like a split anywhere in
    a result are the statutory 50/45/5; everything else is the sentinel."""
    def _numeric_leaves(value, path):
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            found.append((path, value))
        elif isinstance(value, dict):
            for k, v in value.items():
                _numeric_leaves(v, f"{path}.{k}")
        elif isinstance(value, (list, tuple)):
            for i, v in enumerate(value):
                _numeric_leaves(v, f"{path}[{i}]")

    found = []
    _numeric_leaves(result, "result")
    for path, value in found:
        # statutory values may appear under the corpus key (statutory_split)
        # or a checklist entry's quoted copy (entry["split"]).
        in_split_payload = "statutory_split" in path or ".split." in path
        assert value in (50, 45, 5) and in_split_payload, (
            f"numeric value outside a statutory split: {path}={value}"
        )


# ── lookup_recording_societies (pure corpus read) ──────────────────────────────

def test_lookup_us_digital_only_scope_and_mandate():
    res = _run(svc.lookup_recording_societies("US"))
    assert res["status"] == "ok"
    ids = [b["id"] for b in res["recording_bodies"]]
    assert ids == ["soundexchange"]
    sx = res["recording_bodies"][0]
    assert "digital non-interactive only" in sx["scope_notes"].lower()
    assert "International Mandate" in sx["registration_notes"]
    assert "no terrestrial-radio neighbouring right" in res["notes"].lower()
    # composition-side context references Reed's corpus verbatim
    assert set(res["composition_context"]["performance_ids"]) == \
        set(publishing_data.COUNTRY_REGISTRATION["US"]["performance"])
    assert "the_mlc" in res["composition_context"]["mechanical_ids"]


def test_lookup_fr_all_four_bodies_with_roles():
    res = _run(svc.lookup_recording_societies("FR"))
    assert res["status"] == "ok"
    by_id = {b["id"]: b for b in res["recording_bodies"]}
    assert set(by_id) == {"adami", "spedidam", "scpp", "sppf"}
    assert by_id["adami"]["represents"] == "performers"
    assert "featured" in by_id["adami"]["scope_notes"].lower()
    assert by_id["spedidam"]["represents"] == "performers"
    assert "session" in by_id["spedidam"]["scope_notes"].lower()
    assert by_id["scpp"]["represents"] == "rights_owners"
    assert by_id["sppf"]["represents"] == "rights_owners"
    assert "role" in res["notes"].lower()


def test_lookup_nz_recording_side_honest_unknown():
    res = _run(svc.lookup_recording_societies("NZ"))
    assert res["status"] == "ok"
    assert res["recording_bodies"] is None, "a body must never be invented"
    assert res["recording_side_status"] == "unverified"
    assert "verify live" in res["recording_side_note"].lower()
    # the composition side is still honestly reported (APRA AMCOS)
    assert res["composition_context"]["performance_ids"] == ["apra"]


def test_lookup_unknown_country_not_in_corpus():
    res = _run(svc.lookup_recording_societies("BR"))
    assert res["status"] == "country_not_in_corpus"
    assert res["country"] == "BR"
    assert sorted(res["supported_countries"]) == sorted(royalties_data.ROYALTY_COUNTRIES)
    assert "recording_bodies" not in res, "never guess a body"


def test_lookup_case_insensitive():
    res = _run(svc.lookup_recording_societies("  us "))
    assert res["status"] == "ok" and res["country"] == "US"


# ── build_registration_checklist (explicit flags only) ─────────────────────────

def test_checklist_full_us_both_hats_self_published_with_producer():
    res = _run(svc.build_registration_checklist(dict(_FULL_US_SITUATION)))
    assert res["complete"] is True
    assert res["needs"] == []
    assert res["situation"] == _FULL_US_SITUATION

    by_rule = {e["rule_id"]: e for e in res["registrations"]}
    assert list(by_rule) == ["writer_home_pro", "self_published_publisher_registration",
                             "us_catalog_mlc", "masters_rights_owner_registration",
                             "performer_registration", "producers_session_players_lod"], \
        "ordered entries, corpus rule order preserved"

    # writer + publisher memberships route to the US PROs
    assert by_rule["writer_home_pro"]["capacity"] == "writer"
    assert {b["id"] for b in by_rule["writer_home_pro"]["bodies"]} == \
        {"ascap", "bmi", "sesac", "gmr"}
    assert by_rule["self_published_publisher_registration"]["capacity"] == "publisher"

    # the MLC entry is present with the separate-and-free note
    mlc = by_rule["us_catalog_mlc"]
    assert mlc["bodies"][0]["id"] == "the_mlc"
    assert mlc["notes"] == "separate and free"
    assert mlc["stream_id"] == "composition_mechanical"

    # BOTH SoundExchange capacities — rights owner AND performer
    masters = by_rule["masters_rights_owner_registration"]
    performer = by_rule["performer_registration"]
    for entry, capacity in ((masters, "rights_owner"), (performer, "performer")):
        assert entry["capacity"] == capacity
        assert [b["id"] for b in entry["bodies"]] == ["soundexchange"]
        assert entry["stream_id"] == "us_digital_recording_performance"
    assert "International Mandate" in masters["notes"]

    # the LOD entry for the producer
    lod = by_rule["producers_session_players_lod"]
    assert lod["registration"] == "letter_of_direction"
    assert lod["bodies"][0]["id"] == "soundexchange"

    # metadata doctrine reminders ride along
    assert set(res["metadata_reminders"]) == set(royalties_data.METADATA_DOCTRINE)
    _assert_no_non_statutory_split(res)


def test_checklist_missing_flag_needs_gap_branch_not_defaulted():
    # REQUIRED no-fabrication invariant: owns_masters not supplied -> the
    # rights-owner registration must NOT appear (never defaulted to True OR
    # False), and the gap is explicit.
    situation = dict(_FULL_US_SITUATION)
    del situation["owns_masters"]
    res = _run(svc.build_registration_checklist(situation))
    assert res["complete"] is False
    assert "[NEEDS:owns_masters]" in res["needs"]
    rule_ids = [e["rule_id"] for e in res["registrations"]]
    assert "masters_rights_owner_registration" not in rule_ids, (
        "an unsupplied flag must never fire its branch"
    )
    # every other explicitly supplied branch still fired
    assert "performer_registration" in rule_ids
    assert "us_catalog_mlc" in rule_ids


def test_checklist_explicit_false_fires_nothing_and_needs_nothing():
    # explicit False is a supplied answer: no gap, no entry.
    res = _run(svc.build_registration_checklist(
        dict(_FULL_US_SITUATION, owns_masters=False)))
    assert "[NEEDS:owns_masters]" not in res["needs"]
    rule_ids = [e["rule_id"] for e in res["registrations"]]
    assert "masters_rights_owner_registration" not in rule_ids


def test_checklist_empty_situation_all_needs_no_entries():
    res = _run(svc.build_registration_checklist({}))
    assert res["complete"] is False
    assert res["registrations"] == []
    for axis in royalties_data.REGISTRATION_SITUATION_SPEC:
        assert f"[NEEDS:{axis}]" in res["needs"]


def test_checklist_non_us_country_no_us_only_entries():
    res = _run(svc.build_registration_checklist({
        "country_of_residence": "UK",
        "self_published": True,
        "owns_masters": True,
        "performed_on_recording": True,
        "has_producers_or_session_players": False,
    }))
    by_rule = {e["rule_id"]: e for e in res["registrations"]}
    assert "us_catalog_mlc" not in by_rule, "MLC entry is US-connected only"
    # UK recording side routes to PPL in both capacities, split is the sentinel
    masters = by_rule["masters_rights_owner_registration"]
    assert [b["id"] for b in masters["bodies"]] == ["ppl"]
    assert masters["stream_id"] == "recording_performance"
    assert masters["split"] == "varies_verify_with_society"
    _assert_no_non_statutory_split(res)


def test_checklist_nz_recording_side_unverified_not_invented():
    res = _run(svc.build_registration_checklist({
        "country_of_residence": "NZ",
        "self_published": False,
        "owns_masters": True,
        "performed_on_recording": False,
        "has_producers_or_session_players": False,
    }))
    masters = next(e for e in res["registrations"]
                   if e["rule_id"] == "masters_rights_owner_registration")
    assert masters["bodies"] is None
    assert masters["body_status"] == "unverified"
    assert "verify live" in masters["body_note"].lower()


def test_checklist_free_text_is_note_only():
    with_note = dict(_FULL_US_SITUATION, deal_history="had a JV with an indie label")
    res_with = _run(svc.build_registration_checklist(with_note))
    res_without = _run(svc.build_registration_checklist(dict(_FULL_US_SITUATION)))
    note_texts = [n["text"] for n in res_with["notes"]]
    assert "had a JV with an indie label" in note_texts
    # aside from the note itself, the free text changed NOTHING — never parsed
    assert dict(res_with, notes=[]) == dict(res_without, notes=[])


def test_checklist_results_json_serializable():
    for res in (
        _run(svc.build_registration_checklist(dict(_FULL_US_SITUATION))),
        _run(svc.build_registration_checklist({})),
        _run(svc.build_registration_checklist({"country_of_residence": "XX"})),
    ):
        json.dumps(res)


def test_service_source_is_entity_wall_clean():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


def test_service_imports_no_anthropic():
    import ast as _ast
    tree = _ast.parse(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, _ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert "anthropic" not in name.lower(), \
                "service layer must not import the LLM SDK"


# ── Wiring: both new tools through the real /api/chat_stream loop ─────────────

def test_wire_new_tools_dispatch_and_emit_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("LEDGER_LOCK_ACCOUNT_CONNECTED", raising=False)  # NOT portal-gated

    lookup_calls, checklist_calls = [], []
    real_lookup    = m.ledger_lock_service.lookup_recording_societies
    real_checklist = m.ledger_lock_service.build_registration_checklist

    async def rec_lookup(country_code=""):
        lookup_calls.append(country_code)
        return await real_lookup(country_code)

    async def rec_checklist(situation=None):
        checklist_calls.append(situation)
        return await real_checklist(situation)

    monkeypatch.setattr(m.ledger_lock_service, "lookup_recording_societies", rec_lookup)
    monkeypatch.setattr(m.ledger_lock_service, "build_registration_checklist", rec_checklist)

    responses = [
        _Resp([_Block("tool_use", name="lookup_recording_societies",
                      input={"country_code": "US"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_registration_checklist",
                      input={"situation": dict(_FULL_US_SITUATION)}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Here is your registration checklist to review.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ledger-lock",
        "message":   "where does my recording money come from and what do I register",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert lookup_calls == ["US"]
    assert checklist_calls == [dict(_FULL_US_SITUATION)]

    actions_evt = next(e for e in events if e["type"] == "actions")
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert set(by_tool) == {"lookup_recording_societies", "build_registration_checklist"}
    assert "1 recording bod" in by_tool["lookup_recording_societies"]["result"]
    assert "6 registration(s)" in by_tool["build_registration_checklist"]["result"]
    assert "0 gap(s)" in by_tool["build_registration_checklist"]["result"]
    assert actions_evt["ledger_account_not_connected"] is False, \
        "consult tools must not trip the portal gate"
    assert all(kw.get("tools") == m.LEDGER_LOCK_TOOLS for kw in create_calls)


def test_wire_new_tools_not_portal_gated_even_when_expired(monkeypatch, tmp_path):
    # Even the auth-expired gate state must not touch the two consult tools.
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("LEDGER_LOCK_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="lookup_recording_societies",
                      input={"country_code": "FR"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="France splits recording collection by role.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ledger-lock",
        "message":   "who collects recording royalties in France",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["ledger_account_not_connected"] is False
    assert "4 recording bod" in actions_evt["actions_taken"][0]["result"]


def test_ledger_lock_tools_expose_unit2_schemas(monkeypatch, tmp_path):
    # Unit 2 added tools #4 and #5 after the original three; later units may
    # append more (the exact roster is asserted in the newest unit's tests).
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.LEDGER_LOCK_TOOLS]
    assert names[:5] == ["search_royalty_sources", "reconcile_royalty_statement",
                         "file_tax_document", "lookup_recording_societies",
                         "build_registration_checklist"]
    lookup = next(t for t in m.LEDGER_LOCK_TOOLS if t["name"] == "lookup_recording_societies")
    assert lookup["input_schema"]["required"] == ["country_code"]
    checklist = next(t for t in m.LEDGER_LOCK_TOOLS
                     if t["name"] == "build_registration_checklist")
    # Reed Unit-2 precedent: fabrication-risk sub-fields are described, never
    # schema-forced — requiredness is enforced via [NEEDS:] in results.
    assert "required" not in checklist["input_schema"], (
        "schema-forcing the situation would push the model to fabricate flags"
    )
    assert "required" not in checklist["input_schema"]["properties"]["situation"]


def test_dispatch_missing_country_code_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(
        m._execute_ledger_lock_tool("lookup_recording_societies", {}, "artist-9"))
    assert res["status"] == "country_not_in_corpus"
    assert nc is False
    assert summary["result"] == "country_not_in_corpus"


def test_dispatch_checklist_missing_situation_is_all_needs(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(
        m._execute_ledger_lock_tool("build_registration_checklist", {}, "artist-9"))
    assert res["complete"] is False
    assert res["registrations"] == []
    assert nc is False
    assert "0 registration(s)" in summary["result"]
    assert "5 gap(s)" in summary["result"]
