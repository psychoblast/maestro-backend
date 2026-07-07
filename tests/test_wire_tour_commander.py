"""
PROOF tests — Miles (tour-commander) Anthropic tool_use loop, DOC-WRITER Option B.

Proves that, in /api/chat_stream:

  (a) Miles emits lookup_tour_ops_doctrine → build_tour_doc_scaffold then a
      final message; both tour-ops tour_commander_service functions are
      invoked with the correct args and the stream surfaces a populated
      `actions` event, with TOUR_COMMANDER_TOOLS passed on every create() call
      and tour_ops_not_connected ALWAYS False (the old tour-ops-account gate
      is retired);
  (b) a NON-tour agent never receives TOUR_COMMANDER_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool
      loop with MARCUS_TOOLS, never TOUR_COMMANDER_TOOLS;
  (d) the scaffold tool_result fed back to the model carries Miles's standing
      doctrine (documents-not-figures / prep-not-negotiation) and never a
      computed total.

Everything is in-process and deterministic. NO network / LLM calls — the
Anthropic client is faked and the tour_commander_service boundary is exercised
through recording wrappers over the REAL (pure) functions. This file NEVER
asserts generated prose; the final assistant text is scripted.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import tour_ops_data as td


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


# ── (a) Miles runs the tool loop and surfaces actions_taken ──────────────────

def test_tour_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    lookup_calls, build_calls = [], []
    real_lookup = m.tour_commander_service.lookup_tour_ops_doctrine
    real_build  = m.tour_commander_service.build_tour_doc_scaffold

    async def rec_lookup(advancing_key="", day_sheet_field="", settlement_key="",
                          routing_key="", festival_key="", vocabulary_term=""):
        lookup_calls.append({
            "advancing_key": advancing_key, "day_sheet_field": day_sheet_field,
            "settlement_key": settlement_key, "routing_key": routing_key,
            "festival_key": festival_key, "vocabulary_term": vocabulary_term,
        })
        return await real_lookup(advancing_key=advancing_key, day_sheet_field=day_sheet_field,
                                 settlement_key=settlement_key, routing_key=routing_key,
                                 festival_key=festival_key, vocabulary_term=vocabulary_term)

    async def rec_build(doc_type="", inputs=None):
        build_calls.append({"doc_type": doc_type, "inputs": inputs})
        return await real_build(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.tour_commander_service, "lookup_tour_ops_doctrine", rec_lookup)
    monkeypatch.setattr(m.tour_commander_service, "build_tour_doc_scaffold", rec_build)

    scaffold_input = {"deal_memo": "One night headline, per contract."}
    responses = [
        _Resp([_Block("tool_use", name="lookup_tour_ops_doctrine",
                      input={"advancing_key": "venue_advance"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_tour_doc_scaffold",
                      input={"doc_type": "advance_pack", "inputs": scaffold_input},
                      id="t2")], "tool_use"),
        _Resp([_Block("text", text="Here is your advance pack prep.")], "end_turn"),
    ]
    create_calls = []
    tool_result_payloads = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        for msg in kwargs.get("messages", []):
            if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                for blk in msg["content"]:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        tool_result_payloads.append(blk["content"])
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Miles must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "tour-commander",
        "message":   "prep an advance pack for the headline date",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert lookup_calls == [{
        "advancing_key": "venue_advance", "day_sheet_field": "", "settlement_key": "",
        "routing_key": "", "festival_key": "", "vocabulary_term": "",
    }], lookup_calls
    assert build_calls == [{"doc_type": "advance_pack", "inputs": scaffold_input}], build_calls

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["lookup_tour_ops_doctrine", "build_tour_doc_scaffold"], tools_used
    assert actions_evt["tour_ops_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "match(es)" in by_tool["lookup_tour_ops_doctrine"]["result"]
    assert "scaffold_ready" in by_tool["build_tour_doc_scaffold"]["result"]

    # Three create() round-trips; TOUR tools on every one (never MARCUS_TOOLS).
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.TOUR_COMMANDER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)

    # (d) Miles's standing doctrine survives into the tool_result fed back to
    # the model, and no computed total ever leaks through. (json.dumps escapes
    # non-ASCII em-dashes, so compare on the DECODED payload, not the raw string.)
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    decoded = json.loads(scaffold_payload)
    assert decoded["header"]["documents_not_figures"] == td.MILES_DOCTRINE["documents_not_figures"]
    for banned_key in ('"total"', '"gross"', '"net"', '"sum"'):
        assert banned_key not in scaffold_payload.lower()


# ── (b) Non-tour agent never gets tour tools, takes the unchanged path ────────

def test_non_tour_agent_never_receives_tour_tools(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return _Resp([_Block("text", text="x")], "end_turn")

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    monkeypatch.setattr(m.async_client.messages, "stream",
                        lambda **kw: _FakeStream("Here is some general guidance for you."))

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "music-edu",
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert create_calls == [], "non-tour agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not tour tools ──────

def test_marcus_still_uses_marcus_tools_not_tour(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return _Resp([_Block("text", text="On it.")], "end_turn")

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    monkeypatch.setattr(m.async_client.messages, "stream",
                        lambda **kw: (_ for _ in ()).throw(
                            AssertionError("Marcus must not use messages.stream")))

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "puppet-master",
        "message":   "what's my next move",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    assert len(create_calls) == 1
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.TOUR_COMMANDER_TOOLS


# ── (d) day_sheet privacy rule survives the loop, end to end ──────────────────

def test_day_sheet_privacy_rule_survives_the_loop(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    day_sheet_inputs = {
        "doors": "7:00 PM", "curfew": "11:00 PM",
        "artist_hotel_info": "Hotel Regal, room 204",
    }
    responses = [
        _Resp([_Block("tool_use", name="build_tour_doc_scaffold",
                      input={"doc_type": "day_sheet", "inputs": day_sheet_inputs},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is today's day sheet.")], "end_turn"),
    ]
    create_calls = []
    tool_result_payloads = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        for msg in kwargs.get("messages", []):
            if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                for blk in msg["content"]:
                    if isinstance(blk, dict) and blk.get("type") == "tool_result":
                        tool_result_payloads.append(blk["content"])
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "tour-commander",
        "message":   "give me today's day sheet",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    assert "Hotel Regal" not in scaffold_payload  # the sensitive VALUE never rode through
    fields_section = json.loads(scaffold_payload)["sections"][0]
    assert "artist_hotel_info" not in [f["field"] for f in fields_section["fields"]]
