"""
PROOF tests — Mo (mobile-monetize) Anthropic tool_use loop, DOC-WRITER Option B.

Proves that, in /api/chat_stream:

  (a) Mo emits lookup_monetization_doctrine -> build_monetization_doc_scaffold
      then a final message; both mobile_monetize_service functions are
      invoked with the correct args and the stream surfaces a populated
      `actions` event, with MOBILE_MONETIZE_TOOLS passed on every create()
      call and not_connected ALWAYS False (the old platform-monetization-
      account gate is retired);
  (b) a NON-mo agent never receives MOBILE_MONETIZE_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool
      loop with MARCUS_TOOLS, never MOBILE_MONETIZE_TOOLS;
  (d) the scaffold tool_result fed back to the model carries Mo's standing
      doctrine (no_income_projections) and never a computed income figure of
      any kind.

Everything is in-process and deterministic. NO network / LLM calls — the
Anthropic client is faked and the mobile_monetize_service boundary is
exercised through recording wrappers over the REAL (pure) functions. This
file NEVER asserts generated prose; the final assistant text is scripted.
"""
import importlib
import json
import re
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import monetization_data as md


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


# ── (a) Mo runs the tool loop and surfaces actions_taken ──────────────────────

def test_mo_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    lookup_calls, build_calls = [], []
    real_lookup = m.mobile_monetize_service.lookup_monetization_doctrine
    real_build  = m.mobile_monetize_service.build_monetization_doc_scaffold

    async def rec_lookup(stream_key="", diversification_key="", sequencing_key="", admin_key=""):
        lookup_calls.append({
            "stream_key": stream_key, "diversification_key": diversification_key,
            "sequencing_key": sequencing_key, "admin_key": admin_key,
        })
        return await real_lookup(stream_key=stream_key, diversification_key=diversification_key,
                                  sequencing_key=sequencing_key, admin_key=admin_key)

    async def rec_build(doc_type="", inputs=None):
        build_calls.append({"doc_type": doc_type, "inputs": inputs})
        return await real_build(doc_type=doc_type, inputs=inputs)

    monkeypatch.setattr(m.mobile_monetize_service, "lookup_monetization_doctrine", rec_lookup)
    monkeypatch.setattr(m.mobile_monetize_service, "build_monetization_doc_scaffold", rec_build)

    scaffold_inputs = {"active_streams": ["streaming_royalties"], "audience_stage": "has_audience"}
    responses = [
        _Resp([_Block("tool_use", name="lookup_monetization_doctrine",
                      input={"stream_key": "live_performance"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_monetization_doc_scaffold",
                      input={"doc_type": "revenue_map", "inputs": scaffold_inputs},
                      id="t2")], "tool_use"),
        _Resp([_Block("text", text="Here is your revenue map.")], "end_turn"),
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
        raise AssertionError("Mo must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "mobile-monetize",
        "message":   "build me a revenue map",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert lookup_calls == [{
        "stream_key": "live_performance", "diversification_key": "",
        "sequencing_key": "", "admin_key": "",
    }], lookup_calls
    assert build_calls == [{"doc_type": "revenue_map", "inputs": scaffold_inputs}], build_calls

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["lookup_monetization_doctrine", "build_monetization_doc_scaffold"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "index returned" in by_tool["lookup_monetization_doctrine"]["result"] \
        or "not-found" in by_tool["lookup_monetization_doctrine"]["result"]
    assert "section(s) ready" in by_tool["build_monetization_doc_scaffold"]["result"]

    # Three create() round-trips; MO tools on every one (never MARCUS_TOOLS).
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.MOBILE_MONETIZE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)

    # (d) Mo's standing doctrine survives into the tool_result fed back to the
    # model, and no computed income figure ever leaks through. (json.dumps
    # escapes non-ASCII em-dashes, so compare on the DECODED payload, not the
    # raw string.)
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    decoded = json.loads(scaffold_payload)
    assert decoded["header"]["no_income_projections"] == md.MO_DOCTRINE["no_income_projections"]
    for banned_key in ('"total"', '"gross"', '"net"', '"sum"', '"projected_income"',
                       '"estimated_income"', '"income_estimate"'):
        assert banned_key not in scaffold_payload.lower()
    assert not re.search(r"\$\s*\d", scaffold_payload)


# ── (b) Non-mo agent never gets mo tools, takes the unchanged path ────────────

def test_non_mo_agent_never_receives_mo_tools(monkeypatch, tmp_path):
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

    assert create_calls == [], "non-mo agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not mo tools ───────

def test_marcus_still_uses_marcus_tools_not_mo(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.MOBILE_MONETIZE_TOOLS


# ── (d) diversification_plan doctrine survives the loop, end to end ───────────

def test_diversification_plan_doctrine_survives_the_loop_no_income_figure(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    plan_inputs = {"active_streams": ["teaching_and_session_work"], "audience_stage": "pre_audience"}
    responses = [
        _Resp([_Block("tool_use", name="build_monetization_doc_scaffold",
                      input={"doc_type": "diversification_plan", "inputs": plan_inputs},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here is a diversification plan.")], "end_turn"),
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
        "agent_id":  "mobile-monetize",
        "message":   "give me a diversification plan",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    scaffold_payload = next(p for p in tool_result_payloads if "scaffold_ready" in p)
    decoded = json.loads(scaffold_payload)
    assert decoded["doc_type"] == "diversification_plan"
    assert decoded["header"]["diversify_dont_concentrate"] == md.MO_DOCTRINE["diversify_dont_concentrate"]
    for banned_key in ('"total"', '"gross"', '"net"', '"sum"', '"projected_income"'):
        assert banned_key not in scaffold_payload.lower()
    assert not re.search(r"\$\s*\d", scaffold_payload)
