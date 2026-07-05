"""
PROOF tests — Reed Unit 3: build_publishing_doc_scaffold (doc scaffold writer).

Jade-U4 pattern: the tool is DATA-only — compact ingredients, no model call, no
prose. Tests assert structure, section order, and gap markers; generated prose
is NEVER asserted (only the scripted fake final-text substring in the wiring
test). split_sheet reuses the Unit-2 validator for gaps + both 100%-sum checks
(missing share -> sum_not_checkable, remainder NEVER inferred — REQUIRED
invariant). sync_pack asserts one-stop ONLY when all three explicit
confirmations hold (REQUIRED); a directly supplied one_stop_status is
disregarded. Unknown doc_type -> structured error. Wiring: dispatch through
Reed's execute path in the real /api/chat_stream loop, NOT portal-gated.
"""
import asyncio
import importlib
import json
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


def _full_contributor(name, lyrics, music, pub_share):
    return {
        "legal_name": name, "contact": f"{name.lower().replace(' ', '.')}@mail.test",
        "role": "writer", "lyrics_percent": lyrics, "music_percent": music,
        "pro_affiliation": "SOCAN", "writer_ipi": "00111222333",
        "publisher_name": "SELF", "publisher_ipi": "00444555666",
        "publisher_share_percent": pub_share, "signature": "signed",
    }


_SONG = {"song_title": "Northern Line", "date": "2026-07-05", "samples_used": "no"}

_SYNC_FULL = {
    "genre_specific": "dark synth-pop", "moods": "brooding, nocturnal",
    "tempo_bpm": 92, "instrumentation": "analog synths, live bass, drum machine",
    "vocals": "female lead", "similar_artists": "artist comparisons on file",
    "suggested_placements": "late-night drama, thriller trailers",
    "rights_breakdown": "artist controls composition and master",
    "clearance_contact_composition": "mgmt@mail.test",
    "clearance_contact_master": "mgmt@mail.test",
    "stems_available": "yes", "instrumental_available": "yes",
    "clean_version_available": "yes",
    "samples_cleared_declaration": "no samples used",
    "isrc": "AA-AAA-26-00001", "iswc": "T-000000001-1",
    "pro_affiliation": "SOCAN", "ipi": "00111222333",
}

_ALL_CONFIRMED = {
    "master_control_confirmed": True,
    "publishing_control_100_confirmed": True,
    "no_uncleared_samples": True,
}

_EXPECTED_SPLIT_ORDER = ["song", "contributors", "writer_sum_status",
                         "publisher_sum_status", "master_side_extension",
                         "amendment_rule", "signatures"]


# ── split_sheet branch ─────────────────────────────────────────────────────────

def test_split_sheet_full_inputs_ordered_sections_and_sums():
    res = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="split_sheet",
        inputs={"song": dict(_SONG),
                "contributors": [_full_contributor("Ana Reyes", 60, 40, 50),
                                 _full_contributor("Jo Vega", 40, 60, 50)]},
    ))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "split_sheet"
    assert [s["key"] for s in res["sections"]] == _EXPECTED_SPLIT_ORDER
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["writer_sum_status"]["content_or_gap"]["status"] == "sum_ok"
    assert by_key["publisher_sum_status"]["content_or_gap"]["status"] == "sum_ok"
    assert res["missing"] == []
    assert len(by_key["contributors"]["content_or_gap"]) == 2
    assert len(by_key["signatures"]["content_or_gap"]) == 2
    assert res["signed_when"] == publishing_data.SPLIT_SHEET_SPEC["signed_when"]


def test_split_sheet_missing_percent_not_inferred():
    # REQUIRED no-fabrication invariant: Jo's music % missing -> [NEEDS:] gap,
    # sum_not_checkable, and the honest remainder (60) appears NOWHERE.
    jo = _full_contributor("Jo Vega", 40, 0, 50)
    del jo["music_percent"]
    res = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="split_sheet",
        inputs={"song": dict(_SONG),
                "contributors": [_full_contributor("Ana Reyes", 60, 40, 50), jo]},
    ))
    assert "[NEEDS: music_percent for Jo Vega]" in res["missing"]
    by_key = {s["key"]: s for s in res["sections"]}
    writer = by_key["writer_sum_status"]["content_or_gap"]
    assert writer["status"] == "sum_not_checkable"
    assert writer["music"]["total"] is None
    assert "60" not in json.dumps(writer), "remainder must never be inferred"
    # the contributor block carries the same verbatim gap, never a filled value
    jo_block = next(b for b in by_key["contributors"]["content_or_gap"]
                    if b["contributor"] == "Jo Vega")
    assert jo_block["fields"]["music_percent"] == "[NEEDS: music_percent for Jo Vega]"


def test_split_sheet_master_extension_and_amendment_present():
    res = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="split_sheet",
        inputs={"song": dict(_SONG),
                "contributors": [_full_contributor("Ana Reyes", 100, 100, 100)],
                "isrc": "AA-AAA-26-00001"},
    ))
    by_key = {s["key"]: s for s in res["sections"]}
    master = by_key["master_side_extension"]["content_or_gap"]
    assert master["status"] == "best_practice"
    assert master["fields"]["isrc"] == "AA-AAA-26-00001"
    assert master["fields"]["master_ownership_percent"].startswith("[ARTIST-SUPPLIED:")
    assert any("master_ownership_percent" in r for r in res["artist_supplied_reminders"])
    assert by_key["amendment_rule"]["content_or_gap"] == \
        publishing_data.SPLIT_SHEET_SPEC["amendment_rule"]["description"]


# ── sync_pack branch ───────────────────────────────────────────────────────────

def test_sync_pack_all_confirmations_asserts_one_stop():
    res = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="sync_pack",
        inputs=dict(_SYNC_FULL, one_stop_confirmations=dict(_ALL_CONFIRMED)),
    ))
    assert res["status"] == "scaffold_ready"
    assert res["one_stop"]["status"] == "one_stop"
    assert res["one_stop"]["missing_conditions"] == []
    assert res["one_stop"]["rule"] == publishing_data.SYNC_METADATA_SPEC["one_stop_rule"]
    assert res["missing"] == []
    assert res["artist_supplied_reminders"] == []


def test_sync_pack_missing_confirmation_cannot_assert():
    # REQUIRED: any unconfirmed condition -> cannot_assert_one_stop + named.
    partial = dict(_ALL_CONFIRMED)
    del partial["publishing_control_100_confirmed"]
    res = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="sync_pack",
        inputs=dict(_SYNC_FULL, one_stop_confirmations=partial),
    ))
    assert res["one_stop"]["status"] == "cannot_assert_one_stop"
    assert res["one_stop"]["missing_conditions"] == ["publishing_control_100_confirmed"]
    assert any("100% publishing control" in r for r in res["artist_supplied_reminders"])


def test_sync_pack_supplied_one_stop_status_is_disregarded():
    res = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="sync_pack",
        inputs=dict(_SYNC_FULL, one_stop_status="yes, total one-stop"),
    ))
    assert res["one_stop"]["status"] == "cannot_assert_one_stop", (
        "a supplied one_stop_status must never substitute for explicit confirmations"
    )
    assert len(res["one_stop"]["missing_conditions"]) == 3
    assert any(n["field"] == "one_stop_status" and "disregarded" in n["note"]
               for n in res["notes"])


def test_sync_pack_missing_metadata_field_gaps():
    inputs = dict(_SYNC_FULL, one_stop_confirmations=dict(_ALL_CONFIRMED))
    del inputs["tempo_bpm"]
    del inputs["clearance_contact_master"]
    res = _run(svc.build_publishing_doc_scaffold("artist-1", doc_type="sync_pack",
                                                 inputs=inputs))
    assert "[NEEDS: tempo_bpm]" in res["missing"]
    assert "[NEEDS: clearance_contact_master]" in res["missing"]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["core_metadata"]["content_or_gap"]["tempo_bpm"] == "[NEEDS: tempo_bpm]"


def test_sync_pack_field_groups_cover_the_corpus_spec():
    # Drift guard: every corpus-native sync field is either in a group or the
    # computed one_stop_status; the only extra input keys are the two contacts.
    group_fields = {f for g in svc.SYNC_PACK_FIELD_GROUPS for f in g["fields"]}
    spec_fields = {f["field"] for f in publishing_data.SYNC_METADATA_SPEC["fields"]}
    extras = {"clearance_contact_composition", "clearance_contact_master"}
    assert spec_fields == (group_fields - extras) | {"one_stop_status"}


# ── shared behavior ────────────────────────────────────────────────────────────

def test_unknown_doc_type_structured_error():
    res = _run(svc.build_publishing_doc_scaffold("artist-1", doc_type="press_kit",
                                                 inputs={}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == ["split_sheet", "sync_pack"]
    assert "sections" not in res


def test_not_submit_ready_reminder_in_both_branches():
    split = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="split_sheet", inputs={"contributors": []}))
    sync = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="sync_pack", inputs={}))
    for res in (split, sync):
        assert "NOT submit-ready" in res["note"]
        assert "NOT a legal document" in res["note"]


def test_every_scaffold_result_is_json_serializable():
    for res in (
        _run(svc.build_publishing_doc_scaffold("a", doc_type="split_sheet",
                                               inputs={"song": dict(_SONG)})),
        _run(svc.build_publishing_doc_scaffold("a", doc_type="sync_pack", inputs={})),
        _run(svc.build_publishing_doc_scaffold("a", doc_type="nope", inputs={})),
    ):
        json.dumps(res)


def test_unmapped_inputs_ride_along_verbatim():
    res = _run(svc.build_publishing_doc_scaffold(
        "artist-1", doc_type="sync_pack",
        inputs=dict(_SYNC_FULL, one_stop_confirmations=dict(_ALL_CONFIRMED),
                    tour_history="played 40 shows in 2025")))
    assert res["unmapped_inputs"] == {"tour_history": "played 40 shows in 2025"}


def test_service_source_is_entity_wall_clean_unit3():
    import pathlib
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


# ── wiring through the real loop ───────────────────────────────────────────────

def test_wire_scaffold_dispatch_not_portal_gated(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("INK_AND_AIR_CONNECTED", raising=False)

    scaffold_calls = []
    real_scaffold = m.ink_and_air_service.build_publishing_doc_scaffold

    async def rec_scaffold(artist_id, doc_type="", inputs=None):
        scaffold_calls.append({"artist_id": artist_id, "doc_type": doc_type})
        return await real_scaffold(artist_id, doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.ink_and_air_service, "build_publishing_doc_scaffold",
                        rec_scaffold)

    responses = [
        _Resp([_Block("tool_use", name="build_publishing_doc_scaffold",
                      input={"doc_type": "sync_pack",
                             "inputs": dict(_SYNC_FULL,
                                            one_stop_confirmations=dict(_ALL_CONFIRMED))},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is your sync pack draft to review.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ink-and-air",
        "message":   "build my sync pack",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert scaffold_calls == [{"artist_id": "artist-9", "doc_type": "sync_pack"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "build_publishing_doc_scaffold"
    assert "scaffold_ready" in actions_evt["actions_taken"][0]["result"]
    assert "gap(s)" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["not_connected"] is False, "scaffold tool must not trip the gate"
    done_evt = next(e for e in events if e["type"] == "done")
    assert "sync pack draft" in done_evt["full_text"]  # scripted fake text only
    assert all(kw.get("tools") == m.INK_AND_AIR_TOOLS for kw in create_calls)


def test_dispatch_unknown_doc_type_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(m._execute_ink_and_air_tool(
        "build_publishing_doc_scaffold", {"doc_type": "press_kit"}, "artist-9"))
    assert res["status"] == "unknown_doc_type"
    assert summary["result"] == "unknown_doc_type"
    assert nc is False


def test_ink_and_air_tools_now_six(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.INK_AND_AIR_TOOLS]
    assert names == ["search_publishing_deals", "review_split_sheet",
                     "register_composition", "lookup_publishing_societies",
                     "validate_split_sheet", "build_publishing_doc_scaffold"]
    scaffold = next(t for t in m.INK_AND_AIR_TOOLS
                    if t["name"] == "build_publishing_doc_scaffold")
    assert scaffold["input_schema"]["required"] == ["doc_type"]
    assert scaffold["input_schema"]["properties"]["doc_type"]["enum"] == \
        ["split_sheet", "sync_pack"]
    # Unit-2 precedent: fabrication-risk sub-fields are described, never forced
    assert "required" not in scaffold["input_schema"]["properties"]["inputs"]
