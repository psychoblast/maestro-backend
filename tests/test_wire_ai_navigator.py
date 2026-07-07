"""
PROOF tests — Neo (ai-navigator) Anthropic tool_use loop.

Mirrors tests/test_wire_lex_cipher.py. Proves that, in /api/chat_stream:

  (a) Neo emits search_ai_tools -> assess_tech_stack then a final message; both
      mock-first ai_navigator_service functions are invoked with the correct args
      and the stream surfaces a populated `actions` event, with AI_NAVIGATOR_TOOLS
      passed on every create() call;
  (b) a NON-navigator agent never receives AI_NAVIGATOR_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never AI_NAVIGATOR_TOOLS;
  (d) Neo is consult-only — the retired provision_automation mock-action tool (and
      its AI_NAVIGATOR_CONNECTED gate) is gone from both the schema and the
      dispatch: it is neither offered to the model nor executable by name, and
      not_connected is structurally always False.

Everything is in-process and deterministic. NO network / LLM calls — the Anthropic
client is faked and the ai_navigator_service boundary is exercised through
recording wrappers over the REAL (pure, mock-first) functions.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


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


# ── (a) Neo runs the tool loop and surfaces actions_taken ────────────────────

def test_navigator_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    search_calls, assess_calls = [], []
    real_search = m.ai_navigator_service.search_ai_tools
    real_assess = m.ai_navigator_service.assess_tech_stack

    async def rec_search(category="", use_case=""):
        search_calls.append({"category": category, "use_case": use_case})
        return await real_search(category=category, use_case=use_case)

    async def rec_assess(artist_id, current_tools="", goal=""):
        assess_calls.append({"artist_id": artist_id, "current_tools": current_tools, "goal": goal})
        return await real_assess(artist_id, current_tools=current_tools, goal=goal)

    monkeypatch.setattr(m.ai_navigator_service, "search_ai_tools",   rec_search)
    monkeypatch.setattr(m.ai_navigator_service, "assess_tech_stack", rec_assess)

    responses = [
        _Resp([_Block("tool_use", name="search_ai_tools",
                      input={"category": "audio"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="assess_tech_stack",
                      input={"current_tools": "captions only", "goal": "grow"}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — searched tools and assessed your stack.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Neo must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ai-navigator",
        "message":   "help me modernize my tooling",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert search_calls == [{"category": "audio", "use_case": ""}], search_calls
    assert assess_calls == [{
        "artist_id": "artist-9", "current_tools": "captions only", "goal": "grow",
    }], assess_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_ai_tools", "assess_tech_stack"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "tool(s) found" in by_tool["search_ai_tools"]["result"]
    assert "gap(s)" in by_tool["assess_tech_stack"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.AI_NAVIGATOR_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


# ── (b) Non-navigator agent never gets navigator tools ───────────────────────

def test_non_navigator_agent_never_receives_navigator_tools(monkeypatch, tmp_path):
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

    assert create_calls == [], "non-navigator agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS ─────────────────────

def test_marcus_still_uses_marcus_tools_not_navigator(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.AI_NAVIGATOR_TOOLS


# ── (d) Neo's tool roster is consult-only; the retired mock tool cannot reappear ──

def test_ai_navigator_tool_roster_is_consult_only(monkeypatch, tmp_path):
    """This unit owns Neo's exact tool roster: exactly the two consult tools,
    nothing more. The retired provision_automation mock-action tool must not
    reappear."""
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.AI_NAVIGATOR_TOOLS]
    assert names == ["search_ai_tools", "assess_tech_stack"], names
    assert "provision_automation" not in names
    assert not hasattr(m.ai_navigator_service, "provision_automation")
    assert not hasattr(m.ai_navigator_service, "AutomationNotConnected")
    assert not hasattr(m.ai_navigator_service, "AutomationAuthExpired")


def test_ai_navigator_unknown_tool_name_is_handled_gracefully(monkeypatch, tmp_path):
    """A retired/unknown tool name must degrade to the unknown_tool branch, not crash."""
    m = _load_main(monkeypatch, tmp_path)
    import asyncio
    result, summary, not_connected = asyncio.run(
        m._execute_ai_navigator_tool("provision_automation", {"workflow_name": "x"}, "artist-9")
    )
    assert result == {"error": "unknown_tool", "tool": "provision_automation"}
    assert not_connected is False
