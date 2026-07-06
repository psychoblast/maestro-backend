"""
PROOF tests — Cree Unit 2: lookup_copy_conventions (+ wiring).

The lookup is a PURE read over the copy_data corpus (Cree Unit 1) — structure
only, scripted fakes, no live model call anywhere. Each of the seven doc types
returns its spec (bio word ranges / ordered press-release sections / one-sheet
elements + doctrine / EPK core+optional / caption elements + rules), its
conventions, and the full honesty-rule set (this domain is made of facts; no
fact, stat, quote, or comparison is ever invented). bio_long carries its open
upper word bound HONESTLY — (500, None), never a guessed ceiling. Unknown
doc_type -> structured error listing the supported types. Wiring: schema in
CREATIVE_DIRECTOR_TOOLS (exact roster owned here until a newer unit lands),
dispatch through Cree's execute path in the real /api/chat_stream loop, NOT
portal-gated (no CREATIVE_DIRECTOR_STUDIO_CONNECTED needed).
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


_HONESTY_RULE_IDS = ["facts_supplied_or_marked",
                     "quotes_verbatim_with_source_or_omitted",
                     "stats_supplied_only", "comparisons_only_if_supplied",
                     "drafts_not_publish_ready"]


# ── per-doc-type lookups (pure corpus reads) ───────────────────────────────────

def test_bio_types_return_their_specs_with_correct_word_ranges():
    for bio_id, expected_range in (("bio_short", (50, 100)),
                                   ("bio_medium", (200, 300))):
        res = _run(svc.lookup_copy_conventions(bio_id))
        assert res["status"] == "ok"
        assert res["doc_type"] == bio_id
        assert tuple(res["spec"]["word_range"]) == expected_range
        assert res["spec"] == dict(copy_data.BIO_SPECS[bio_id])
        conv_ids = {c["id"] for c in res["conventions"]}
        assert conv_ids == set(copy_data.BIO_CONVENTIONS)


def test_bio_long_carries_open_upper_bound_honestly():
    res = _run(svc.lookup_copy_conventions("bio_long"))
    assert res["status"] == "ok"
    lower, upper = res["spec"]["word_range"]
    assert lower == 500
    assert upper is None, "the open upper bound must ride through — never a guessed ceiling"


def test_press_release_returns_ordered_sections_and_conventions():
    res = _run(svc.lookup_copy_conventions("press_release"))
    assert res["status"] == "ok"
    assert [s["key"] for s in res["spec"]["sections"]] == \
        [s["key"] for s in copy_data.PRESS_RELEASE_SPEC["sections"]]
    assert [c["id"] for c in res["conventions"]] == \
        ["front_load_for_skimming", "quotes_only_real_and_attributed",
         "one_release_one_news_item"]


def test_one_sheet_returns_elements_and_doctrine_with_offered_choice():
    res = _run(svc.lookup_copy_conventions("one_sheet"))
    assert res["status"] == "ok"
    assert [e["key"] for e in res["spec"]["elements"]] == \
        [e["key"] for e in copy_data.ONE_SHEET_SPEC["elements"]]
    skip = next(c for c in res["conventions"]
                if c["id"] == "skip_unimpressive_stats")
    assert skip["choice_type"] == "offered_to_artist"
    assert skip["never"] == "silent_edit"


def test_epk_outline_returns_core_and_optional_components():
    res = _run(svc.lookup_copy_conventions("epk_outline"))
    assert res["status"] == "ok"
    assert [c["key"] for c in res["spec"]["core_components"]] == \
        [c["key"] for c in copy_data.EPK_OUTLINE_SPEC["core_components"]]
    assert [c["key"] for c in res["spec"]["optional_components"]] == \
        [c["key"] for c in copy_data.EPK_OUTLINE_SPEC["optional_components"]]
    assert {d["id"] for d in res["conventions"]} == \
        {"decision_tool_not_scrapbook", "tailor_per_audience"}


def test_caption_set_returns_elements_and_no_invented_urgency_rule():
    res = _run(svc.lookup_copy_conventions("caption_set"))
    assert res["status"] == "ok"
    assert [e["key"] for e in res["spec"]["elements"]] == \
        ["hook_line", "context_line", "cta", "tag_link_placeholders"]
    assert [r["id"] for r in res["conventions"]] == \
        ["no_invented_urgency_or_milestones"]


def test_honesty_rules_ride_along_on_every_doc_type():
    for dt in copy_data.COPY_DOC_TYPES:
        res = _run(svc.lookup_copy_conventions(dt))
        assert res["status"] == "ok", dt
        assert [r["id"] for r in res["honesty_rules"]] == _HONESTY_RULE_IDS, dt


def test_unknown_doc_type_structured_error():
    for bad in ("biography", "", None):
        res = _run(svc.lookup_copy_conventions(bad))
        assert res["status"] == "unknown_doc_type"
        assert res["supported_doc_types"] == list(copy_data.COPY_DOC_TYPES)
        assert "spec" not in res


def test_doc_type_normalized_case_and_whitespace():
    res = _run(svc.lookup_copy_conventions("  Press_Release "))
    assert res["status"] == "ok"
    assert res["doc_type"] == "press_release"


def test_every_lookup_result_is_json_serializable():
    for dt in list(copy_data.COPY_DOC_TYPES) + ["nope"]:
        json.dumps(_run(svc.lookup_copy_conventions(dt)))


def test_service_source_is_entity_wall_clean_unit2():
    assert_no_forbidden_terms(pathlib.Path(svc.__file__).read_text(encoding="utf-8"))


def test_service_imports_no_anthropic_unit2():
    # Service layer imports no LLM SDK — AST-enforced (Nadia precedent).
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

def test_creative_director_tools_include_lookup(monkeypatch, tmp_path):
    # Prefix-only here — the NEWEST unit owns the exact roster
    # (test_cree_unit3, Reed/Nadia precedent).
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.CREATIVE_DIRECTOR_TOOLS]
    assert names[:4] == ["search_rollout_templates", "assess_creative_concept",
                         "schedule_rollout", "lookup_copy_conventions"]
    lookup = next(t for t in m.CREATIVE_DIRECTOR_TOOLS
                  if t["name"] == "lookup_copy_conventions")
    assert lookup["input_schema"]["required"] == ["doc_type"]
    assert lookup["input_schema"]["properties"]["doc_type"]["enum"] == \
        list(copy_data.COPY_DOC_TYPES)


def test_wire_lookup_dispatch_not_portal_gated(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("CREATIVE_DIRECTOR_STUDIO_CONNECTED", raising=False)

    lookup_calls = []
    real_lookup = m.creative_director_service.lookup_copy_conventions

    async def rec_lookup(doc_type=""):
        lookup_calls.append({"doc_type": doc_type})
        return await real_lookup(doc_type)

    monkeypatch.setattr(m.creative_director_service, "lookup_copy_conventions",
                        rec_lookup)

    responses = [
        _Resp([_Block("tool_use", name="lookup_copy_conventions",
                      input={"doc_type": "press_release"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here are the press release conventions to work from.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "creative-director",
        "message":   "how should a press release be structured?",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    assert lookup_calls == [{"doc_type": "press_release"}]
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["actions_taken"][0]["tool"] == "lookup_copy_conventions"
    assert "honesty rule(s)" in actions_evt["actions_taken"][0]["result"]
    assert actions_evt["creative_studio_not_connected"] is False, \
        "the lookup tool must not trip the studio gate"
    done_evt = next(e for e in events if e["type"] == "done")
    assert "press release conventions" in done_evt["full_text"]  # scripted fake text only
    assert all(kw.get("tools") == m.CREATIVE_DIRECTOR_TOOLS for kw in create_calls)


def test_dispatch_unknown_doc_type_through_execute_path(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    res, summary, nc = asyncio.run(m._execute_creative_director_tool(
        "lookup_copy_conventions", {"doc_type": "biography"}, "artist-9"))
    assert res["status"] == "unknown_doc_type"
    assert summary["result"] == "unknown_doc_type"
    assert nc is False
