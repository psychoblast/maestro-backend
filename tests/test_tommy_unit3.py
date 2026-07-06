"""
PROOF tests — Tommy Unit 3: build_release_doc_scaffold (release doc scaffold writer).

Jade-U4 / Reed-U3 / Nadia-U3 / Cree-U3 pattern (option B): the tool is DATA-only
— compact ingredients, no model call, no prose. Tests assert structure, field
order, and gap markers; generated prose is NEVER asserted. THE HARD RULE OF THIS
DOMAIN is the spine of this file: no identifier (ISRC/UPC), date, or credit is
ever generated — every field is the supplied input VERBATIM, a [NEEDS:<fact>]
gap, or an [ARTIST-SUPPLIED:<confirm>] reminder. REQUIRED no-fabrication
invariants: an absent per-track ISRC surfaces as [NEEDS:isrc_track_N] — a gap,
NEVER a generated code; a supplied artist_name passes through BYTE-EXACT (no
case normalization — the exact-match doctrine forbids "fixing" it). Unknown
doc_type -> structured error. Wiring: dispatch through Tommy's execute path in
the real /api/chat_stream loop, NOT portal-gated; the newest unit owns the exact
tool roster (Reed/Nadia/Cree precedent — six tools).
"""
import asyncio
import importlib
import json
import pathlib
import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import release_data
import label_services_service as svc
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


_HONESTY_RULE_IDS = ["specs_are_current_conventions_verify_live",
                     "never_invent_identifier_date_or_credit",
                     "no_strategy_as_fact",
                     "legal_licensing_routes_elsewhere"]

_FULL_RELEASE_LEVEL = {
    "release_title": "Silo Sessions",
    "artist_name": "mara VOSS",  # deliberately odd casing — must ride byte-exact
    "upc": "0123456789012",
    "release_date": "2026-09-04",
    "genre_subgenre": "dream pop / synth pop",
    "label_name": "Grain Silo Records",
    "p_line": "2026 Mara Voss",
    "c_line": "2026 Mara Voss",
    "year": "2026",
    "territories": "worldwide",
}

_FULL_TRACK = {
    "track_title": "Grain Light",
    "isrc": "USABC2600001",
    "songwriter_credits": "Mara Voss (BMI)",
    "language": "English",
    "explicit_flag": "not explicit",
}


# ── metadata_sheet branch ──────────────────────────────────────────────────────

def test_metadata_sheet_release_level_order_and_verbatim():
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(_FULL_RELEASE_LEVEL, tracks=[dict(_FULL_TRACK)])))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "metadata_sheet"
    assert [s["key"] for s in res["release_level"]] == \
        [f["field"] for f in release_data.METADATA_FIELDS["release_level"]]
    by_key = {s["key"]: s for s in res["release_level"]}
    assert by_key["release_title"]["content_or_gap"] == "Silo Sessions"
    assert by_key["upc"]["content_or_gap"] == "0123456789012"


def test_artist_name_passes_through_byte_exact():
    # REQUIRED no-fabrication invariant: a supplied artist name rides VERBATIM —
    # no case normalization, no "fixing". The exact-match doctrine forbids it.
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(_FULL_RELEASE_LEVEL, tracks=[dict(_FULL_TRACK)])))
    by_key = {s["key"]: s for s in res["release_level"]}
    assert by_key["artist_name"]["content_or_gap"] == "mara VOSS"  # byte-exact


def test_metadata_sheet_per_track_sections_and_fields():
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(_FULL_RELEASE_LEVEL, tracks=[dict(_FULL_TRACK)])))
    assert len(res["tracks"]) == 1
    track = res["tracks"][0]
    assert track["track"] == 1
    assert [f["key"] for f in track["fields"]] == \
        [f["field"] for f in release_data.METADATA_FIELDS["track_level"]]
    by_key = {f["key"]: f for f in track["fields"]}
    assert by_key["track_title"]["content_or_gap"] == "Grain Light"
    assert by_key["isrc"]["content_or_gap"] == "USABC2600001"


def test_absent_isrc_is_gap_never_generated():
    # REQUIRED: an absent per-track ISRC is a [NEEDS:isrc_track_N] slot — never a
    # generated code. Two tracks; the second has no ISRC.
    t2 = {k: v for k, v in _FULL_TRACK.items() if k != "isrc"}
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(_FULL_RELEASE_LEVEL, tracks=[dict(_FULL_TRACK), t2])))
    track2 = res["tracks"][1]
    by_key = {f["key"]: f for f in track2["fields"]}
    assert by_key["isrc"]["content_or_gap"] == "[NEEDS:isrc_track_2]"
    assert "[NEEDS:isrc_track_2]" in res["missing"]
    # the gap slot holds no fabricated code — nothing that looks like an ISRC
    assert by_key["isrc"]["content_or_gap"] == "[NEEDS:isrc_track_2]"
    # track 1's real code is present; track 2's is genuinely absent, not minted
    assert json.dumps(track2).count("USABC") == 0


def test_explicit_flag_unset_carries_doctrine_and_gap():
    t = {k: v for k, v in _FULL_TRACK.items() if k != "explicit_flag"}
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(_FULL_RELEASE_LEVEL, tracks=[t])))
    by_key = {f["key"]: f for f in res["tracks"][0]["fields"]}
    flag = by_key["explicit_flag"]
    assert flag["content_or_gap"] == "[NEEDS:explicit_flag]"
    assert "explicit" in flag["doctrine"].lower()
    assert "own isrc" in flag["doctrine"].lower()


def test_optional_track_fields_are_artist_supplied_confirms_not_hard_gaps():
    # version/features/roles/lyrics are optional — absent, they come back as
    # [ARTIST-SUPPLIED:] confirms, not [NEEDS:] gaps.
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(_FULL_RELEASE_LEVEL, tracks=[dict(_FULL_TRACK)])))
    by_key = {f["key"]: f for f in res["tracks"][0]["fields"]}
    for opt in ("version_field", "featured_artists",
                "producer_contributor_roles", "lyrics_optional"):
        assert str(by_key[opt]["content_or_gap"]).startswith("[ARTIST-SUPPLIED:")
    # and none of them polluted the hard-gap list
    for opt in ("version_field", "featured_artists",
                "producer_contributor_roles", "lyrics_optional"):
        assert f"[NEEDS:{opt}]" not in res["missing"]


def test_territories_absent_is_artist_supplied_confirm():
    inputs = {k: v for k, v in _FULL_RELEASE_LEVEL.items() if k != "territories"}
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(inputs, tracks=[dict(_FULL_TRACK)])))
    by_key = {s["key"]: s for s in res["release_level"]}
    assert str(by_key["territories"]["content_or_gap"]).startswith("[ARTIST-SUPPLIED:")
    assert "[NEEDS:territories]" not in res["missing"]


def test_metadata_sheet_no_tracks_is_a_gap():
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet", inputs=dict(_FULL_RELEASE_LEVEL)))
    assert res["tracks"] == []
    assert "[NEEDS:tracks]" in res["missing"]


def test_track_count_builds_empty_gap_slots():
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet",
        inputs=dict(_FULL_RELEASE_LEVEL, track_count=3)))
    assert len(res["tracks"]) == 3
    # each track's ISRC is its own indexed gap — no code invented
    for i in (1, 2, 3):
        by_key = {f["key"]: f for f in res["tracks"][i - 1]["fields"]}
        assert by_key["isrc"]["content_or_gap"] == f"[NEEDS:isrc_track_{i}]"


def test_metadata_sheet_missing_release_fields_are_gaps():
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet", inputs={"track_count": 1}))
    for field in ("release_title", "artist_name", "upc", "release_date",
                  "genre_subgenre", "label_name", "p_line", "c_line", "year"):
        assert f"[NEEDS:{field}]" in res["missing"]


# ── release_record branch ──────────────────────────────────────────────────────

def test_release_record_sections_and_mapping():
    inputs = {
        "title": "Silo Sessions", "artist_spelling": "Mara Voss",
        "upc": "0123456789012", "distributor": "SomeDistro",
        "master_owner": "Mara Voss",
    }
    res = _run(svc.build_release_doc_scaffold(doc_type="release_record", inputs=inputs))
    assert res["status"] == "scaffold_ready"
    assert [s["key"] for s in res["sections"]] == \
        [f["field"] for f in release_data.RELEASE_RECORD_SPEC["fields"]]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["title"]["content_or_gap"] == "Silo Sessions"
    assert by_key["release_date"]["content_or_gap"] == "[NEEDS:release_date]"
    assert "[NEEDS:isrc_per_track]" in res["missing"]


# ── shared behavior ────────────────────────────────────────────────────────────

def test_unknown_doc_type_structured_error():
    res = _run(svc.build_release_doc_scaffold(doc_type="liner_notes", inputs={}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(svc.RELEASE_DOC_TYPES)
    assert "release_level" not in res and "sections" not in res


def test_not_submit_ready_reminder_and_honesty_rules_on_both_branches():
    for dt in svc.RELEASE_DOC_TYPES:
        res = _run(svc.build_release_doc_scaffold(doc_type=dt, inputs={"track_count": 1}))
        assert res["status"] == "scaffold_ready", dt
        assert "not submit-ready" in res["note"].lower(), dt
        assert "byte-exact" in res["note"].lower(), dt
        assert [r["id"] for r in res["honesty_rules"]] == _HONESTY_RULE_IDS, dt


def test_unmapped_inputs_ride_along_verbatim():
    res = _run(svc.build_release_doc_scaffold(
        doc_type="release_record",
        inputs={"title": "Silo Sessions", "studio_notes": "tracked in the silo"}))
    assert res["unmapped_inputs"] == {"studio_notes": "tracked in the silo"}


def test_no_fabricated_codes_anywhere_when_all_absent():
    # Nothing supplied -> the whole scaffold is gaps/confirms; not a single
    # generated identifier appears (no sha1-style hex code).
    res = _run(svc.build_release_doc_scaffold(
        doc_type="metadata_sheet", inputs={"track_count": 2}))
    blob = json.dumps(res)
    assert re.search(r"\b[0-9a-f]{10,}\b", blob) is None
    assert re.search(r"DIST-[0-9A-F]{10}", blob) is None


def test_every_scaffold_result_is_json_serializable():
    for dt in list(svc.RELEASE_DOC_TYPES) + ["nope"]:
        json.dumps(_run(svc.build_release_doc_scaffold(doc_type=dt, inputs={"track_count": 1})))


def test_service_source_is_entity_wall_clean_unit3():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


def test_service_imports_no_anthropic_unit3():
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

def test_label_services_tools_now_six_exact_roster(monkeypatch, tmp_path):
    # Reed/Nadia/Cree Unit-3 precedent: the NEWEST unit owns the EXACT roster.
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.LABEL_SERVICES_TOOLS]
    assert names == ["search_distribution_requirements", "validate_release_metadata",
                     "deliver_to_dsps", "lookup_release_requirements",
                     "build_release_checklist", "build_release_doc_scaffold"]
    scaffold = next(t for t in m.LABEL_SERVICES_TOOLS
                    if t["name"] == "build_release_doc_scaffold")
    assert scaffold["input_schema"]["required"] == ["doc_type"]
    assert scaffold["input_schema"]["properties"]["doc_type"]["enum"] == \
        list(svc.RELEASE_DOC_TYPES)
    # inputs are described, never hard-required (forcing them invites fabrication)
    assert "required" not in scaffold["input_schema"]["properties"]["inputs"]


def test_wire_scaffold_dispatch_not_portal_gated(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("LABEL_SERVICES_CONNECTED", raising=False)

    scaffold_calls = []
    real_scaffold = m.label_services_service.build_release_doc_scaffold

    async def rec_scaffold(doc_type="", inputs=None):
        scaffold_calls.append({"doc_type": doc_type})
        return await real_scaffold(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.label_services_service, "build_release_doc_scaffold",
                        rec_scaffold)

    responses = [
        _Resp([_Block("tool_use", name="build_release_doc_scaffold",
                      input={"doc_type": "metadata_sheet",
                             "inputs": dict(_FULL_RELEASE_LEVEL,
                                            tracks=[dict(_FULL_TRACK)])},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is your metadata sheet to review.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "label-services",
        "message":   "build my metadata sheet",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert scaffold_calls == [{"doc_type": "metadata_sheet"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "build_release_doc_scaffold"
    assert "scaffold_ready" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["not_connected"] is False, \
        "the scaffold tool must not trip the distributor gate"
    done_evt = next(e for e in events if e["type"] == "done")
    assert "metadata sheet" in done_evt["full_text"]  # scripted fake text only
    assert all(kw.get("tools") == m.LABEL_SERVICES_TOOLS for kw in create_calls)


def test_dispatch_unknown_doc_type_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(m._execute_label_services_tool(
        "build_release_doc_scaffold", {"doc_type": "liner_notes"}, "artist-9"))
    assert res["status"] == "unknown_doc_type"
    assert summary["result"] == "unknown_doc_type"
    assert nc is False
