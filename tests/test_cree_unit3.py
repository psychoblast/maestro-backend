"""
PROOF tests — Cree Unit 3: build_copy_scaffold (copy scaffold writer).

Jade-U4 / Reed-U3 / Nadia-U3 pattern (option B): the tool is DATA-only —
compact ingredients, no model call, no prose. Tests assert structure, section
order, and gap markers; generated prose is NEVER asserted (only the scripted
fake final-text substring in the wiring test). THE HARD RULE OF THIS DOMAIN is
the spine of this file: every fact slot is the supplied input VERBATIM, a
[NEEDS:<fact>] gap, or an [ARTIST-SUPPLIED: ...] reminder — REQUIRED
no-fabrication invariants: a press-release quote missing its source becomes
[NEEDS:quote_source] with the quote text WITHHELD from the quote slot; a
one-sheet with an empty stats block surfaces skip_unimpressive_stats as an
OFFERED structural choice (never a silent edit, never auto-decided); a missing
bio fact surfaces as [NEEDS:<fact>], never filled. Unknown doc_type ->
structured error. Wiring: dispatch through Cree's execute path in the real
/api/chat_stream loop, NOT portal-gated; the newest unit owns the exact tool
roster (Reed/Nadia precedent).
"""
import asyncio
import importlib
import json
import pathlib
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import copy_data
import creative_director_service as svc
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
        # Same re-bake as test_reed_unit2 / test_nadia_unit3: earlier r-test
        # files leave '/data' baked into the DB_PATH-caching service modules,
        # crashing main reload.
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


_FULL_BIO_MEDIUM_INPUTS = {
    "artist_name": "Mara Voss",
    "hometown_or_scene": "the Portland DIY scene",
    "genre_or_sound": "analog-synth dream pop",
    "distinctive_hook": "records every vocal take in a disused grain silo",
    "current_project": "the EP 'Silo Sessions'",
    "achievements": "supplied by artist: two regional festival slots in spring",
}

_FULL_PRESS_RELEASE_INPUTS = {
    "headline": "Mara Voss announces 'Silo Sessions' EP",
    "city": "Portland, OR",
    "date": "2026-09-04",
    "news_item": "Mara Voss releases the 'Silo Sessions' EP on September fourth.",
    "supporting_context": "The EP was tracked live in a disused grain silo.",
    "quote": "I wanted the room itself to sing.",
    "quote_source": "Mara Voss, artist statement supplied for this release",
    "short_bio": "Mara Voss is an analog-synth dream pop artist from Portland.",
    "boilerplate": "About Mara Voss: supplied standing paragraph.",
    "contact_name": "Rey Alba",
    "contact_role": "manager",
    "contact_email": "rey.alba@mail.test",
    "music_link": "https://listen.test/silo-sessions",
    "press_photos_link": "https://photos.test/mara-voss",
}


# ── bio branches ───────────────────────────────────────────────────────────────

def test_bio_medium_full_inputs_ordered_ingredients_no_needs():
    res = _run(svc.build_copy_scaffold(
        doc_type="bio_medium", inputs=dict(_FULL_BIO_MEDIUM_INPUTS)))
    assert res["status"] == "scaffold_ready"
    assert res["doc_type"] == "bio_medium"
    assert [s["key"] for s in res["sections"]] == [
        "artist_name", "hometown_or_scene", "genre_or_sound",
        "distinctive_hook", "current_project", "achievements",
    ]
    assert res["missing"] == []
    # every slot is the supplied input VERBATIM
    by_key = {s["key"]: s for s in res["sections"]}
    for field, value in _FULL_BIO_MEDIUM_INPUTS.items():
        assert by_key[field]["content_or_gap"] == value
    assert not any(str(s["content_or_gap"]).startswith("[NEEDS:")
                   for s in res["sections"])


def test_bio_missing_fact_surfaces_needs_never_filled():
    # REQUIRED: a missing fact (hometown) is an explicit gap — never filled.
    inputs = dict(_FULL_BIO_MEDIUM_INPUTS)
    del inputs["hometown_or_scene"]
    res = _run(svc.build_copy_scaffold(doc_type="bio_medium", inputs=inputs))
    assert "[NEEDS:hometown_or_scene]" in res["missing"]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["hometown_or_scene"]["content_or_gap"] == "[NEEDS:hometown_or_scene]"


def test_bio_reminders_carry_word_range_and_conventions():
    # bio branches enforce nothing about prose — the word range and the
    # shared conventions ride along as reminders for Cree's own writing turn.
    for bio_id, expected_range in (("bio_short", [50, 100]),
                                   ("bio_medium", [200, 300]),
                                   ("bio_long", [500, None])):
        res = _run(svc.build_copy_scaffold(doc_type=bio_id, inputs={}))
        assert res["reminders"]["word_range"] == expected_range, bio_id
        conv_ids = {c["id"] for c in res["reminders"]["conventions"]}
        assert conv_ids == set(copy_data.BIO_CONVENTIONS), bio_id


def test_bio_slot_sets_scale_with_length():
    assert [s["key"] for s in
            _run(svc.build_copy_scaffold(doc_type="bio_short", inputs={}))["sections"]] == \
        ["artist_name", "genre_or_sound", "distinctive_hook"]
    long_keys = [s["key"] for s in
                 _run(svc.build_copy_scaffold(doc_type="bio_long", inputs={}))["sections"]]
    assert "origin_story" in long_keys and "artistic_direction" in long_keys


def test_bio_quote_opener_only_with_source():
    # Same quote discipline as press_release: no source -> withheld + gap.
    inputs = dict(_FULL_BIO_MEDIUM_INPUTS,
                  press_quote="a synth revelation", press_quote_source="Fake Weekly, review supplied by artist")
    res = _run(svc.build_copy_scaffold(doc_type="bio_medium", inputs=inputs))
    opener = next(s for s in res["sections"] if s["key"] == "press_quote_opener")
    assert opener["content_or_gap"] == {"quote": "a synth revelation",
                                        "source": "Fake Weekly, review supplied by artist"}

    inputs = dict(_FULL_BIO_MEDIUM_INPUTS, press_quote="a synth revelation")
    res = _run(svc.build_copy_scaffold(doc_type="bio_medium", inputs=inputs))
    assert "[NEEDS:press_quote_source]" in res["missing"]
    assert "press_quote_opener" not in [s["key"] for s in res["sections"]]
    assert "a synth revelation" not in json.dumps(res["sections"])


# ── press_release branch ───────────────────────────────────────────────────────

def test_press_release_full_inputs_sections_in_fixed_order_no_needs():
    res = _run(svc.build_copy_scaffold(
        doc_type="press_release", inputs=dict(_FULL_PRESS_RELEASE_INPUTS)))
    assert res["status"] == "scaffold_ready"
    assert [s["key"] for s in res["sections"]] == \
        [s["key"] for s in copy_data.PRESS_RELEASE_SPEC["sections"]]
    assert res["missing"] == []
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["headline"]["content_or_gap"] == _FULL_PRESS_RELEASE_INPUTS["headline"]
    assert by_key["dateline"]["content_or_gap"] == {"city": "Portland, OR",
                                                    "date": "2026-09-04"}
    quote_slot = by_key["para_2_supporting_context"]["content_or_gap"]["quote"]
    assert quote_slot == {"quote": _FULL_PRESS_RELEASE_INPUTS["quote"],
                          "source": _FULL_PRESS_RELEASE_INPUTS["quote_source"]}


def test_press_release_quote_without_source_withheld():
    # REQUIRED no-fabrication invariant: a supplied quote missing its source
    # -> [NEEDS:quote_source], and the quote text is ABSENT from the quote
    # slot — a quote is never included unattributed.
    inputs = dict(_FULL_PRESS_RELEASE_INPUTS)
    del inputs["quote_source"]
    res = _run(svc.build_copy_scaffold(doc_type="press_release", inputs=inputs))
    assert "[NEEDS:quote_source]" in res["missing"]
    by_key = {s["key"]: s for s in res["sections"]}
    quote_slot = by_key["para_2_supporting_context"]["content_or_gap"]["quote"]
    assert quote_slot == "[NEEDS:quote_source]"
    assert inputs["quote"] not in json.dumps(res["sections"]), \
        "the unattributed quote must be withheld from the scaffold"
    # withheld loudly, not silently — a note explains why
    assert any(n["source"] == "quote" for n in res["notes"])


def test_press_release_no_quote_supplied_slot_is_none_not_a_gap():
    inputs = dict(_FULL_PRESS_RELEASE_INPUTS)
    del inputs["quote"]
    del inputs["quote_source"]
    res = _run(svc.build_copy_scaffold(doc_type="press_release", inputs=inputs))
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["para_2_supporting_context"]["content_or_gap"]["quote"] is None
    assert res["missing"] == []  # quotes are optional — no gap when none exists


def test_press_release_missing_fields_all_gaps():
    res = _run(svc.build_copy_scaffold(doc_type="press_release", inputs={}))
    for field in ("headline", "city", "date", "news_item", "supporting_context",
                  "short_bio", "boilerplate", "contact_name", "contact_role",
                  "contact_email", "music_link", "press_photos_link"):
        assert f"[NEEDS:{field}]" in res["missing"]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["for_immediate_release_line"]["content_or_gap"] == \
        "FOR IMMEDIATE RELEASE"  # structural convention, not an artist fact


# ── one_sheet branch ───────────────────────────────────────────────────────────

_ONE_SHEET_BASE = {
    "artist_name": "Mara Voss",
    "genre": "dream pop",
    "press_photo_link": "https://photos.test/mara-voss",
    "short_bio": "Mara Voss is an analog-synth dream pop artist from Portland.",
    "press_quotes": "supplied quote block with citations, verbatim",
    "social_streaming_links": "https://links.test/maravoss",
    "contact_name": "Rey Alba",
    "contact_role": "manager",
}


def test_one_sheet_supplied_stats_pass_through_verbatim():
    inputs = dict(_ONE_SHEET_BASE, stats="artist-supplied highlights block, verbatim")
    res = _run(svc.build_copy_scaffold(doc_type="one_sheet", inputs=inputs))
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["highlights_stats_block"]["content_or_gap"] == \
        "artist-supplied highlights block, verbatim"
    assert "offered_choice" not in by_key["highlights_stats_block"]
    assert res["offered_choices"] == []


def test_one_sheet_empty_stats_offers_skip_choice_never_silently_dropped():
    # REQUIRED invariant: an empty stats block surfaces the
    # skip-unimpressive-stats doctrine as an OFFERED structural choice — the
    # element stays on the page as an explicit gap and the choice is never
    # auto-decided.
    res = _run(svc.build_copy_scaffold(doc_type="one_sheet",
                                       inputs=dict(_ONE_SHEET_BASE)))
    by_key = {s["key"]: s for s in res["sections"]}
    stats = by_key["highlights_stats_block"]
    assert stats["content_or_gap"] == "[NEEDS:stats]", \
        "the element must never be silently dropped"
    assert stats["offered_choice"]["id"] == "skip_unimpressive_stats"
    assert stats["offered_choice"]["choice_type"] == "offered_to_artist"
    assert stats["offered_choice"]["never"] == "silent_edit"
    assert [c["id"] for c in res["offered_choices"]] == ["skip_unimpressive_stats"]
    assert "[NEEDS:stats]" in res["missing"]


def test_one_sheet_element_order_matches_corpus_and_optional_blocks():
    res = _run(svc.build_copy_scaffold(doc_type="one_sheet", inputs={}))
    assert [s["key"] for s in res["sections"]] == \
        [e["key"] for e in copy_data.ONE_SHEET_SPEC["elements"]]
    by_key = {s["key"]: s for s in res["sections"]}
    # optional blocks come back as ARTIST-SUPPLIED confirms, not NEEDS gaps
    assert str(by_key["release_block_optional"]["content_or_gap"]).startswith(
        "[ARTIST-SUPPLIED:")
    assert str(by_key["press_quotes_with_citation"]["content_or_gap"]).startswith(
        "[ARTIST-SUPPLIED:")
    assert len(res["artist_supplied_reminders"]) == 2


def test_one_sheet_partial_release_block_gaps_its_missing_subfields():
    inputs = dict(_ONE_SHEET_BASE, stats="supplied", release_title="Silo Sessions")
    res = _run(svc.build_copy_scaffold(doc_type="one_sheet", inputs=inputs))
    by_key = {s["key"]: s for s in res["sections"]}
    block = by_key["release_block_optional"]["content_or_gap"]
    assert block["title"] == "Silo Sessions"
    assert block["date"] == "[NEEDS:release_date]"
    assert block["one_sentence"] == "[NEEDS:release_one_sentence]"


# ── epk_outline / caption_set branches ─────────────────────────────────────────

def test_epk_core_sections_ordered_and_optionals_listed_not_hidden():
    res = _run(svc.build_copy_scaffold(doc_type="epk_outline", inputs={}))
    assert [s["key"] for s in res["sections"]] == \
        [c["key"] for c in copy_data.EPK_OUTLINE_SPEC["core_components"]]
    # nothing supplied -> every optional component is LISTED as not included
    assert [c["key"] for c in res["optional_components_not_included"]] == \
        [c["key"] for c in copy_data.EPK_OUTLINE_SPEC["optional_components"]]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["bio_all_lengths"]["content_or_gap"] == {
        "bio_short": "[NEEDS:bio_short]", "bio_medium": "[NEEDS:bio_medium]",
        "bio_long": "[NEEDS:bio_long]"}
    doctrine_ids = {d["id"] for d in res["reminders"]["doctrine"]}
    assert doctrine_ids == {"decision_tool_not_scrapbook", "tailor_per_audience"}


def test_epk_supplied_optional_component_rides_verbatim():
    inputs = {"tour_dates": "supplied dates block, verbatim"}
    res = _run(svc.build_copy_scaffold(doc_type="epk_outline", inputs=inputs))
    tour = next(s for s in res["sections"] if s["key"] == "tour_dates")
    assert tour["content_or_gap"] == "supplied dates block, verbatim"
    assert "tour_dates" not in [c["key"] for c in
                                res["optional_components_not_included"]]


def test_caption_set_elements_and_no_invented_urgency_reminder():
    res = _run(svc.build_copy_scaffold(
        doc_type="caption_set",
        inputs={"hook_line": "supplied hook", "cta": "pre-save via the supplied link"}))
    assert [s["key"] for s in res["sections"]] == \
        ["hook_line", "context_line", "cta", "tag_link_placeholders"]
    by_key = {s["key"]: s for s in res["sections"]}
    assert by_key["hook_line"]["content_or_gap"] == "supplied hook"
    assert by_key["context_line"]["content_or_gap"] == "[NEEDS:context_line]"
    assert [r["id"] for r in res["reminders"]["rules"]] == \
        ["no_invented_urgency_or_milestones"]


# ── shared behavior ────────────────────────────────────────────────────────────

def test_unknown_doc_type_structured_error():
    res = _run(svc.build_copy_scaffold(doc_type="newsletter", inputs={}))
    assert res["status"] == "unknown_doc_type"
    assert res["supported_doc_types"] == list(copy_data.COPY_DOC_TYPES)
    assert "sections" not in res


def test_drafts_not_publish_ready_reminder_on_every_branch():
    for dt in copy_data.COPY_DOC_TYPES:
        res = _run(svc.build_copy_scaffold(doc_type=dt, inputs={}))
        assert res["status"] == "scaffold_ready", dt
        assert "never publish-ready" in res["note"], dt
        assert "NEVER invent" in res["note"], dt


def test_unmapped_inputs_ride_along_verbatim_on_every_branch():
    for dt in copy_data.COPY_DOC_TYPES:
        res = _run(svc.build_copy_scaffold(
            doc_type=dt, inputs={"studio_notes": "tracked in the silo, verbatim"}))
        assert res["unmapped_inputs"] == \
            {"studio_notes": "tracked in the silo, verbatim"}, dt


def test_every_scaffold_result_is_json_serializable():
    for dt in list(copy_data.COPY_DOC_TYPES) + ["nope"]:
        json.dumps(_run(svc.build_copy_scaffold(doc_type=dt, inputs={})))


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
    monkeypatch.delenv("CREATIVE_DIRECTOR_STUDIO_CONNECTED", raising=False)

    scaffold_calls = []
    real_scaffold = m.creative_director_service.build_copy_scaffold

    async def rec_scaffold(doc_type="", inputs=None):
        scaffold_calls.append({"doc_type": doc_type})
        return await real_scaffold(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.creative_director_service, "build_copy_scaffold",
                        rec_scaffold)

    responses = [
        _Resp([_Block("tool_use", name="build_copy_scaffold",
                      input={"doc_type": "bio_medium",
                             "inputs": dict(_FULL_BIO_MEDIUM_INPUTS)},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is your bio draft to review.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "creative-director",
        "message":   "draft my medium bio",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert scaffold_calls == [{"doc_type": "bio_medium"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "build_copy_scaffold"
    assert "scaffold_ready" in actions_evt["actions_taken"][0]["result"]
    assert "gap(s)" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["creative_studio_not_connected"] is False, \
        "the scaffold tool must not trip the studio gate"
    done_evt = next(e for e in events if e["type"] == "done")
    assert "bio draft" in done_evt["full_text"]  # scripted fake text only
    assert all(kw.get("tools") == m.CREATIVE_DIRECTOR_TOOLS for kw in create_calls)


def test_dispatch_unknown_doc_type_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(m._execute_creative_director_tool(
        "build_copy_scaffold", {"doc_type": "newsletter"}, "artist-9"))
    assert res["status"] == "unknown_doc_type"
    assert summary["result"] == "unknown_doc_type"
    assert nc is False


def test_creative_director_tools_now_five(monkeypatch, tmp_path):
    # Reed/Nadia Unit-3 precedent: the NEWEST unit owns the EXACT tool roster.
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.CREATIVE_DIRECTOR_TOOLS]
    assert names == ["search_rollout_templates", "assess_creative_concept",
                     "schedule_rollout", "lookup_copy_conventions",
                     "build_copy_scaffold"]
    scaffold = next(t for t in m.CREATIVE_DIRECTOR_TOOLS
                    if t["name"] == "build_copy_scaffold")
    assert scaffold["input_schema"]["required"] == ["doc_type"]
    assert scaffold["input_schema"]["properties"]["doc_type"]["enum"] == \
        list(copy_data.COPY_DOC_TYPES)
    # Reed/Nadia precedent: fact fields are described, never hard-required —
    # forcing them would push the model to fabricate.
    assert "required" not in scaffold["input_schema"]["properties"]["inputs"]
