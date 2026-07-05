"""
PROOF tests — Reed Unit 2: society lookup + structured split-sheet validation.

Service layer: lookup_publishing_societies is a pure read of the Unit-1 corpus
(publishing_data) — CA's two RROs, the US pick-ONE-PRO rule with the MLC on the
mechanical side, DE's unified CMO, the shared Nordic NCB, and an honest
country_not_in_corpus for anything outside the 11 covered codes.
validate_split_sheet enforces SPLIT_SHEET_SPEC as data: missing required fields
become [NEEDS: ...] gaps, percentage sums are arithmetic on SUPPLIED values only
(a missing share -> sum_not_checkable, remainder NEVER inferred — the
no-fabrication invariant test is REQUIRED), publisher 'SELF' is valid, and free
text passes through as notes, never parsed. review_split_sheet now routes
through validate_split_sheet — the keyword heuristics are gone.

Wiring: both new tools dispatch through _execute_ink_and_air_tool inside the
real /api/chat_stream loop (faked Anthropic client, Jade seam), and neither is
gated on INK_AND_AIR_CONNECTED. Zero network / LLM.
"""
import asyncio
import importlib
import json
import pathlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import ink_and_air_service as svc
import publishing_data
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
        # Earlier test files (test_r26/27/28/30) reload pitch_service /
        # social_service with no DB_PATH set, baking '/data/memory.db' into
        # their module-level _DB_PATH; main's module-level init_*_db() calls
        # then mkdir('/data') -> PermissionError on reload. Re-bake every
        # service module main initializes at import time with THIS test's
        # tmp-path env before reloading main.
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


def _full_contributor(name, lyrics, music, pub_share, publisher="Bright Ideas Pub"):
    return {
        "legal_name": name, "contact": f"{name.lower().replace(' ', '.')}@mail.test",
        "role": "writer", "lyrics_percent": lyrics, "music_percent": music,
        "pro_affiliation": "SOCAN", "writer_ipi": "00111222333",
        "publisher_name": publisher, "publisher_ipi": "00444555666",
        "publisher_share_percent": pub_share, "signature": "signed",
    }


_FULL_SONG = {"song_title": "Northern Line", "date": "2026-07-05", "samples_used": "no"}


# ── lookup_publishing_societies (pure corpus read) ─────────────────────────────

def test_lookup_ca_two_rros():
    res = _run(svc.lookup_publishing_societies("CA"))
    assert res["status"] == "ok"
    assert [s["id"] for s in res["performance"]] == ["socan"]
    assert sorted(s["id"] for s in res["mechanical"]) == ["cmrra", "socan_rr"]
    assert res["unified_cmo"] is False
    assert res["writer_must_choose_one_pro"] is False


def test_lookup_us_pick_one_pro_rule_and_mlc():
    res = _run(svc.lookup_publishing_societies("US"))
    assert res["status"] == "ok"
    assert res["writer_must_choose_one_pro"] is True
    assert "pro_choice_rule" in res
    assert res["pro_choice_rule"] == publishing_data.COUNTRY_REGISTRATION["US"]["notes"]
    assert len(res["performance"]) == 4
    mech_ids = [s["id"] for s in res["mechanical"]]
    assert "the_mlc" in mech_ids
    invite_only = {s["id"] for s in res["performance"] if s["membership_model"] == "invite_only"}
    assert invite_only == {"sesac", "gmr"}


def test_lookup_de_unified_cmo():
    res = _run(svc.lookup_publishing_societies("DE"))
    assert res["status"] == "ok"
    assert res["unified_cmo"] is True
    assert [s["id"] for s in res["performance"]] == ["gema"]
    assert [s["id"] for s in res["mechanical"]] == ["gema"]


def test_lookup_se_ncb_mechanical():
    res = _run(svc.lookup_publishing_societies("SE"))
    assert res["status"] == "ok"
    assert [s["id"] for s in res["performance"]] == ["stim"]
    assert [s["id"] for s in res["mechanical"]] == ["ncb"]


def test_lookup_unknown_country_not_in_corpus():
    res = _run(svc.lookup_publishing_societies("BR"))
    assert res["status"] == "country_not_in_corpus"
    assert res["country"] == "BR"
    assert sorted(res["supported_countries"]) == sorted(publishing_data.PUBLISHING_COUNTRIES)
    assert "performance" not in res and "mechanical" not in res, "never guess a society"


def test_lookup_case_insensitive_and_doctrine_present():
    res = _run(svc.lookup_publishing_societies("  ca "))
    assert res["status"] == "ok" and res["country"] == "CA"
    assert res["doctrine"]["home_society_once"] == publishing_data.DOCTRINE["home_society_once"]


# ── validate_split_sheet (structured; corpus-spec-driven) ──────────────────────

def test_validate_full_valid_sheet():
    res = _run(svc.validate_split_sheet(
        "artist-1", song=dict(_FULL_SONG),
        contributors=[_full_contributor("Ana Reyes", 60, 40, 50),
                      _full_contributor("Jo Vega", 40, 60, 50)],
    ))
    assert res["valid_structure"] is True
    assert res["needs"] == []
    assert res["sum_status"]["writer"]["status"] == "sum_ok"
    assert res["sum_status"]["writer"]["lyrics"]["total"] == 100
    assert res["sum_status"]["writer"]["music"]["total"] == 100
    assert res["sum_status"]["publisher"]["status"] == "sum_ok"
    assert res["sum_status"]["publisher"]["total"] == 100


def test_validate_missing_writer_percent_not_inferred():
    # REQUIRED no-fabrication invariant: Ana has music 40; Jo's music share is
    # missing. The honest remainder (60) must NOT appear anywhere — the side is
    # sum_not_checkable with an explicit [NEEDS: ...] gap instead.
    jo = _full_contributor("Jo Vega", 40, 0, 50)
    del jo["music_percent"]
    res = _run(svc.validate_split_sheet(
        "artist-1", song=dict(_FULL_SONG),
        contributors=[_full_contributor("Ana Reyes", 60, 40, 50), jo],
    ))
    assert res["valid_structure"] is False
    assert "[NEEDS: music_percent for Jo Vega]" in res["needs"]
    writer = res["sum_status"]["writer"]
    assert writer["status"] == "sum_not_checkable"
    assert writer["music"]["status"] == "sum_not_checkable"
    assert writer["music"]["total"] is None, "no partial total that invites inference"
    assert writer["music"].get("rule_id") == "sum_checks_supplied_only"
    assert "60" not in json.dumps(res["sum_status"]), "remainder must never be inferred"
    # the fully-supplied lyrics axis is still honestly reported
    assert writer["lyrics"]["status"] == "sum_ok"


def test_validate_sum_mismatch():
    res = _run(svc.validate_split_sheet(
        "artist-1", song=dict(_FULL_SONG),
        contributors=[_full_contributor("Ana Reyes", 60, 50, 50),
                      _full_contributor("Jo Vega", 50, 50, 50)],
    ))
    assert res["valid_structure"] is False
    assert res["sum_status"]["writer"]["status"] == "sum_mismatch"
    assert res["sum_status"]["writer"]["lyrics"]["total"] == 110


def test_validate_publisher_self_handled():
    res = _run(svc.validate_split_sheet(
        "artist-1", song=dict(_FULL_SONG),
        contributors=[_full_contributor("Ana Reyes", 100, 100, 100, publisher="SELF")],
    ))
    assert res["valid_structure"] is True
    assert not any("publisher_name" in n for n in res["needs"])
    assert res["sum_status"]["publisher"]["status"] == "sum_ok"


def test_validate_free_text_note_passes_through_unparsed():
    with_note = _full_contributor("Ana Reyes", 100, 100, 100)
    with_note["residency"] = "spends half the year in Berlin, tax resident DE"
    res_with = _run(svc.validate_split_sheet(
        "artist-1", song=dict(_FULL_SONG), contributors=[with_note]))
    res_without = _run(svc.validate_split_sheet(
        "artist-1", song=dict(_FULL_SONG),
        contributors=[_full_contributor("Ana Reyes", 100, 100, 100)]))
    note_texts = [n["text"] for n in res_with["notes"]]
    assert "spends half the year in Berlin, tax resident DE" in note_texts
    # aside from the note itself, the free text changed NOTHING — never parsed
    res_with_stripped = dict(res_with, notes=[])
    res_without_stripped = dict(res_without, notes=[])
    assert res_with_stripped == res_without_stripped


def test_validate_empty_contributors():
    res = _run(svc.validate_split_sheet("artist-1", song={}, contributors=[]))
    assert res["valid_structure"] is False
    assert any("contributors" in n for n in res["needs"])
    assert "[NEEDS: song_title]" in res["needs"]
    assert res["sum_status"]["writer"]["status"] == "sum_not_checkable"
    assert res["sum_status"]["publisher"]["status"] == "sum_not_checkable"


def test_validate_samples_yes_requires_sources():
    song = dict(_FULL_SONG, samples_used="yes")
    res = _run(svc.validate_split_sheet(
        "artist-1", song=song,
        contributors=[_full_contributor("Ana Reyes", 100, 100, 100)]))
    assert any("sample_sources" in n for n in res["needs"])


def test_validate_spec_reminders_sourced_from_corpus():
    res = _run(svc.validate_split_sheet("artist-1", song={}, contributors=[]))
    spec = publishing_data.SPLIT_SHEET_SPEC
    assert res["spec_reminders"]["signed_when"] == spec["signed_when"]
    assert res["spec_reminders"]["amendment_rule"] == spec["amendment_rule"]["description"]
    assert spec["master_side_extension"]["rationale"] in res["spec_reminders"]["master_side_extension"]


def test_review_split_sheet_routes_through_validation_heuristics_gone():
    assert not hasattr(svc, "_INK_AND_AIR_HEUR"), "keyword heuristics must be gone"
    res = _run(svc.review_split_sheet("artist-1", split_text="no signature, splits verbal",
                                      context="pre-release"))
    assert "validation" in res
    assert res["finding_count"] == len(res["validation"]["needs"]) > 0
    assert res["recommendation"] == "provide_structured_split_fields"
    # the free text rode through as an unparsed note, and produced no keyword findings
    note_texts = [n["text"] for n in res["validation"]["notes"]]
    assert "no signature, splits verbal" in note_texts
    assert "findings" not in res


def test_service_source_is_entity_wall_clean():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


# ── Wiring: both new tools through the real /api/chat_stream loop ─────────────

def test_wire_new_tools_dispatch_and_emit_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("INK_AND_AIR_CONNECTED", raising=False)  # NOT portal-gated

    lookup_calls, validate_calls = [], []
    real_lookup   = m.ink_and_air_service.lookup_publishing_societies
    real_validate = m.ink_and_air_service.validate_split_sheet

    async def rec_lookup(country_code=""):
        lookup_calls.append(country_code)
        return await real_lookup(country_code)

    async def rec_validate(artist_id, song=None, contributors=None, free_text=""):
        validate_calls.append({"artist_id": artist_id, "contributors": contributors})
        return await real_validate(artist_id, song=song, contributors=contributors,
                                   free_text=free_text)

    monkeypatch.setattr(m.ink_and_air_service, "lookup_publishing_societies", rec_lookup)
    monkeypatch.setattr(m.ink_and_air_service, "validate_split_sheet", rec_validate)

    contributors = [_full_contributor("Ana Reyes", 100, 100, 100)]
    responses = [
        _Resp([_Block("tool_use", name="lookup_publishing_societies",
                      input={"country_code": "US"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="validate_split_sheet",
                      input={"song": dict(_FULL_SONG), "contributors": contributors},
                      id="t2")], "tool_use"),
        _Resp([_Block("text", text="Here is where you register and your sheet checks out.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ink-and-air",
        "message":   "where do I register and check my split sheet",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert lookup_calls == ["US"]
    assert len(validate_calls) == 1 and len(validate_calls[0]["contributors"]) == 1

    actions_evt = next(e for e in events if e["type"] == "actions")
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert set(by_tool) == {"lookup_publishing_societies", "validate_split_sheet"}
    assert "performance" in by_tool["lookup_publishing_societies"]["result"]
    assert "valid_structure=True" in by_tool["validate_split_sheet"]["result"]
    assert actions_evt["not_connected"] is False, "consult tools must not trip the portal gate"
    assert all(kw.get("tools") == m.INK_AND_AIR_TOOLS for kw in create_calls)


def test_wire_new_tools_not_portal_gated_even_when_expired(monkeypatch, tmp_path):
    # Even the auth-expired gate state must not touch the two consult tools.
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("INK_AND_AIR_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="lookup_publishing_societies",
                      input={"country_code": "DE"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="GEMA covers both streams in Germany.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ink-and-air",
        "message":   "where do I register in Germany",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is False
    assert actions_evt["actions_taken"][0]["result"].startswith("1 performance")


def test_ink_and_air_tools_now_five_with_new_schemas(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.INK_AND_AIR_TOOLS]
    assert names == ["search_publishing_deals", "review_split_sheet", "register_composition",
                     "lookup_publishing_societies", "validate_split_sheet"]
    lookup = next(t for t in m.INK_AND_AIR_TOOLS if t["name"] == "lookup_publishing_societies")
    assert lookup["input_schema"]["required"] == ["country_code"]
    validate = next(t for t in m.INK_AND_AIR_TOOLS if t["name"] == "validate_split_sheet")
    assert validate["input_schema"]["required"] == ["contributors"]
    # the never-invent guard: share/IPI sub-fields are described, NOT schema-forced
    item_schema = validate["input_schema"]["properties"]["contributors"]["items"]
    assert "required" not in item_schema, (
        "schema-forcing contributor fields would push the model to fabricate them"
    )


def test_dispatch_missing_country_code_is_structured(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(
        m._execute_ink_and_air_tool("lookup_publishing_societies", {}, "artist-9"))
    assert res["status"] == "country_not_in_corpus"
    assert nc is False
    assert summary["result"] == "country_not_in_corpus"
