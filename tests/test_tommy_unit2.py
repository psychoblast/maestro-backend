"""
PROOF tests — Tommy Unit 2: lookup_release_requirements + build_release_checklist (+ wiring).

Both tools are DATA-only over the release_data corpus (Tommy Unit 1) — no live
model call anywhere. lookup_release_requirements is a pure read: each of the six
topics returns its corpus section plus the full honesty-rule set; an unknown
topic returns a structured error. build_release_checklist is deterministic: it
orders the timeline doctrine (upload -> editorial pitch -> pre-release ->
post-release), carries the ink-and-air cross-refs, and maps each unsupplied axis
to an explicit [NEEDS:<axis>] gap — NEVER defaulted. REQUIRED invariants:
weeks_to_release inside the four-week lead attaches a timeline_already_inside_lead
warning WITHOUT inventing a compressed schedule; an unsupplied axis is a
[NEEDS:] gap, never silently defaulted. Wiring: schemas in LABEL_SERVICES_TOOLS
(prefix-only here — the newest unit owns the exact roster), dispatch through
Tommy's execute path in the real /api/chat_stream loop, NOT portal-gated.
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
        # Same re-bake as test_cree_unit2: earlier r-test files leave '/data'
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


_HONESTY_RULE_IDS = ["specs_are_current_conventions_verify_live",
                     "never_invent_identifier_date_or_credit",
                     "no_strategy_as_fact",
                     "legal_licensing_routes_elsewhere"]

_FULL_CHECKLIST_INPUTS = dict(release_type="ep", weeks_to_release=8,
                              first_release=False)


# ── lookup_release_requirements (pure corpus reads) ────────────────────────────

def test_each_topic_returns_its_section():
    expected = {
        "identifiers": release_data.IDENTIFIER_RULES,
        "metadata": release_data.METADATA_FIELDS,
        "artwork": release_data.ARTWORK_SPEC,
        "timeline": release_data.TIMELINE_DOCTRINE,
        "release_record": release_data.RELEASE_RECORD_SPEC,
        "distributor_switch": release_data.DISTRIBUTOR_SWITCH_MECHANISM,
    }
    for topic, section in expected.items():
        res = _run(svc.lookup_release_requirements(topic))
        assert res["status"] == "ok", topic
        assert res["topic"] == topic
        assert res["data"] == section


def test_honesty_rules_ride_along_on_every_topic():
    for topic in svc.RELEASE_TOPICS:
        res = _run(svc.lookup_release_requirements(topic))
        assert [r["id"] for r in res["honesty_rules"]] == _HONESTY_RULE_IDS, topic


def test_identifiers_topic_carries_isrc_new_vs_same_rules():
    res = _run(svc.lookup_release_requirements("identifiers"))
    isrc = res["data"]["isrc"]
    assert "distributor_switch" in isrc["same_when"]
    assert "remix" in isrc["new_when"]


def test_unknown_topic_structured_error():
    for bad in ("codes", "", None):
        res = _run(svc.lookup_release_requirements(bad))
        assert res["status"] == "unknown_topic"
        assert res["supported_topics"] == list(svc.RELEASE_TOPICS)
        assert "data" not in res


def test_topic_normalized_case_and_whitespace():
    res = _run(svc.lookup_release_requirements("  Distributor_Switch "))
    assert res["status"] == "ok"
    assert res["topic"] == "distributor_switch"


def test_lookup_results_json_serializable():
    for topic in list(svc.RELEASE_TOPICS) + ["nope"]:
        json.dumps(_run(svc.lookup_release_requirements(topic)))


# ── build_release_checklist ────────────────────────────────────────────────────

def test_full_inputs_ordered_checklist_no_missing_no_warnings():
    res = _run(svc.build_release_checklist(**_FULL_CHECKLIST_INPUTS))
    assert res["status"] == "ok"
    assert res["release_type"] == "ep"
    assert res["weeks_to_release"] == 8
    assert res["first_release"] is False
    assert res["missing"] == []
    assert res["warnings"] == []
    steps = [i["step"] for i in res["checklist"]]
    # upload -> editorial -> the four pre-release items -> the post-release items
    assert steps == [
        "upload_to_distributor", "editorial_pitch",
        "dashboard_access_verified", "release_shows_as_upcoming",
        "split_sheet_signed_before_upload", "stems_archived_for_sync",
        "verify_live_on_every_platform", "save_codes_to_master_record",
        "links_match_metadata",
    ]


def test_cross_refs_to_ink_and_air_present_in_checklist():
    res = _run(svc.build_release_checklist(**_FULL_CHECKLIST_INPUTS))
    split = next(i for i in res["checklist"]
                 if i["step"] == "split_sheet_signed_before_upload")
    assert "ink-and-air" in split["cross_ref"].lower()
    assert "ink-and-air" in res["cross_refs"]["stems_archived_for_sync"].lower()


def test_weeks_inside_lead_warns_without_inventing_a_schedule():
    # REQUIRED: weeks_to_release=2 -> timeline_already_inside_lead warning is
    # present AND no invented compressed schedule (the checklist stays the
    # standard doctrine; no fabricated day-by-day dates).
    res = _run(svc.build_release_checklist(release_type="single",
                                           weeks_to_release=2, first_release=True))
    warn_ids = [w["id"] for w in res["warnings"]]
    assert "timeline_already_inside_lead" in warn_ids
    warn = next(w for w in res["warnings"]
                if w["id"] == "timeline_already_inside_lead")
    assert "not silently re-plan" in warn["message"].lower() \
        or "do not silently" in warn["message"].lower()
    # the checklist is the standard doctrine — not a fabricated compressed plan
    steps = [i["step"] for i in res["checklist"]]
    ample = _run(svc.build_release_checklist(release_type="single",
                                             weeks_to_release=12, first_release=True))
    assert steps == [i["step"] for i in ample["checklist"]]
    assert "compressed_schedule" not in res
    # no invented concrete dates anywhere in the result
    assert re.search(r"\d{4}-\d{2}-\d{2}", json.dumps(res)) is None


def test_unsupplied_axes_are_needs_gaps_never_defaulted():
    # REQUIRED: an unsupplied axis surfaces as [NEEDS:<axis>] and is never
    # silently defaulted (release_type is NOT quietly set to 'single').
    res = _run(svc.build_release_checklist())
    assert res["release_type"] == "[NEEDS:release_type]"
    assert res["weeks_to_release"] == "[NEEDS:weeks_to_release]"
    assert res["first_release"] == "[NEEDS:first_release]"
    for gap in ("[NEEDS:release_type]", "[NEEDS:weeks_to_release]",
                "[NEEDS:first_release]"):
        assert gap in res["missing"]
    # with no weeks supplied there is no inside-the-lead warning (can't warn
    # on data we don't have)
    assert res["warnings"] == []


def test_invalid_release_type_is_a_gap_not_a_guess():
    res = _run(svc.build_release_checklist(release_type="mixtape",
                                           weeks_to_release=6, first_release=False))
    assert res["release_type"] == "[NEEDS:release_type]"
    assert "[NEEDS:release_type]" in res["missing"]


def test_first_release_true_prepends_profile_claim_step():
    res = _run(svc.build_release_checklist(release_type="album",
                                           weeks_to_release=10, first_release=True))
    assert res["checklist"][0]["step"] == "claim_artist_profiles"
    # not present when it is not the first release
    res2 = _run(svc.build_release_checklist(release_type="album",
                                            weeks_to_release=10, first_release=False))
    assert res2["checklist"][0]["step"] == "upload_to_distributor"


def test_checklist_honesty_rules_and_note():
    res = _run(svc.build_release_checklist(**_FULL_CHECKLIST_INPUTS))
    assert [r["id"] for r in res["honesty_rules"]] == _HONESTY_RULE_IDS
    assert "verify" in res["note"].lower()
    assert "never defaulted" in res["note"].lower()


def test_checklist_results_json_serializable():
    for kwargs in ({}, dict(release_type="single", weeks_to_release=1,
                            first_release=True), _FULL_CHECKLIST_INPUTS):
        json.dumps(_run(svc.build_release_checklist(**kwargs)))


# ── service-module guarantees ──────────────────────────────────────────────────

def test_service_source_is_entity_wall_clean_unit2():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


def test_service_imports_no_anthropic_unit2():
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

def test_label_services_tools_include_new_tools(monkeypatch, tmp_path):
    # Prefix-only here — the NEWEST unit (Unit 3) owns the exact roster.
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.LABEL_SERVICES_TOOLS]
    assert names[:5] == ["search_distribution_requirements",
                         "validate_release_metadata", "deliver_to_dsps",
                         "lookup_release_requirements", "build_release_checklist"]
    lookup = next(t for t in m.LABEL_SERVICES_TOOLS
                  if t["name"] == "lookup_release_requirements")
    assert lookup["input_schema"]["required"] == ["topic"]
    assert lookup["input_schema"]["properties"]["topic"]["enum"] == \
        list(svc.RELEASE_TOPICS)
    checklist = next(t for t in m.LABEL_SERVICES_TOOLS
                     if t["name"] == "build_release_checklist")
    # axes are described, never hard-required (forcing them invites fabrication)
    assert "required" not in checklist["input_schema"]


def test_wire_lookup_dispatch_not_portal_gated(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("LABEL_SERVICES_CONNECTED", raising=False)

    lookup_calls = []
    real_lookup = m.label_services_service.lookup_release_requirements

    async def rec_lookup(topic=""):
        lookup_calls.append({"topic": topic})
        return await real_lookup(topic)

    monkeypatch.setattr(m.label_services_service, "lookup_release_requirements",
                        rec_lookup)

    responses = [
        _Resp([_Block("tool_use", name="lookup_release_requirements",
                      input={"topic": "identifiers"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here are the identifier rules to work from.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "label-services",
        "message":   "what are the ISRC rules?",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert lookup_calls == [{"topic": "identifiers"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "lookup_release_requirements"
    assert "honesty rule(s)" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["not_connected"] is False, \
        "the lookup tool must not trip the distributor gate"
    done_evt = next(e for e in events if e["type"] == "done")
    assert "identifier rules" in done_evt["full_text"]  # scripted fake text only
    assert all(kw.get("tools") == m.LABEL_SERVICES_TOOLS for kw in create_calls)


def test_dispatch_checklist_and_unknown_topic_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(m._execute_label_services_tool(
        "build_release_checklist",
        {"release_type": "single", "weeks_to_release": 2, "first_release": True},
        "artist-9"))
    assert res["status"] == "ok"
    assert "warning(s)" in summary["result"]
    assert nc is False

    res2, summary2, nc2 = asyncio.run(m._execute_label_services_tool(
        "lookup_release_requirements", {"topic": "nope"}, "artist-9"))
    assert res2["status"] == "unknown_topic"
    assert summary2["result"] == "unknown_topic"
    assert nc2 is False
