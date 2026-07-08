"""
PROOF tests — Coach (live-coach) Anthropic tool_use loop.

Mirrors tests/test_wire_lex_cipher.py. Proves that, in /api/chat_stream:
(a) Coach emits search_coaching_drills -> assess_stage_presence then a final message
and surfaces a populated `actions` event with LIVE_COACH_TOOLS on every create();
(b) a non-target agent never receives LIVE_COACH_TOOLS; (c) the gate is exclusive
(Marcus still uses MARCUS_TOOLS); (d) Coach is consult-only — the retired
schedule_coaching_session mock-action tool (and its LIVE_COACH_CONNECTED gate) is
gone from both the schema and the dispatch: it is neither offered to the model nor
executable by name, and not_connected is structurally always False.
Zero network / LLM — the Anthropic client is faked and the live_coach_service
boundary is exercised through recording wrappers over the REAL (pure, mock-first)
functions.
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


def test_live_coach_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    f1_calls, f2_calls = [], []
    real_f1 = m.live_coach_service.search_coaching_drills
    real_f2 = m.live_coach_service.assess_stage_presence

    async def rec_f1(focus="", level=""):
        f1_calls.append({"focus": focus, "level": level})
        return await real_f1(focus=focus, level=level)

    async def rec_f2(artist_id, performance_notes="", context=""):
        f2_calls.append({"artist_id": artist_id, "performance_notes": performance_notes, "context": context})
        return await real_f2(artist_id, performance_notes=performance_notes, context=context)

    monkeypatch.setattr(m.live_coach_service, "search_coaching_drills", rec_f1)
    monkeypatch.setattr(m.live_coach_service, "assess_stage_presence", rec_f2)

    responses = [
        _Resp([_Block("tool_use", name="search_coaching_drills", input={"focus": "vocals"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="assess_stage_presence",
                      input={"performance_notes": "stares at floor", "context": "ctx"}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — took the actions across both tools.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Coach must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "live-coach",
        "message":   "take some actions for me",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert f1_calls == [{"focus": "vocals", "level": ""}], f1_calls
    assert f2_calls == [{"artist_id": "artist-9", "performance_notes": "stares at floor", "context": "ctx"}], f2_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_coaching_drills", "assess_stage_presence"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "drill(s) found" in by_tool["search_coaching_drills"]["result"]
    assert "issue(s)" in by_tool["assess_stage_presence"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.LIVE_COACH_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_live_coach_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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

    assert create_calls == [], "non-target agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


def test_live_coach_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.LIVE_COACH_TOOLS


def test_live_coach_tool_roster_is_consult_only(monkeypatch, tmp_path):
    """This unit owns Coach's exact tool roster: exactly the two consult tools,
    nothing more. The retired schedule_coaching_session mock-action tool must not
    reappear."""
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.LIVE_COACH_TOOLS]
    assert names == ["search_coaching_drills", "assess_stage_presence"], names
    assert "schedule_coaching_session" not in names
    assert not hasattr(m.live_coach_service, "schedule_coaching_session")
    assert not hasattr(m.live_coach_service, "CoachingCalendarNotConnected")
    assert not hasattr(m.live_coach_service, "CoachingCalendarAuthExpired")


def test_live_coach_unknown_tool_name_is_handled_gracefully(monkeypatch, tmp_path):
    """A retired/unknown tool name must degrade to the unknown_tool branch, not crash."""
    m = _load_main(monkeypatch, tmp_path)
    import asyncio
    result, summary, not_connected = asyncio.run(
        m._execute_live_coach_tool("schedule_coaching_session", {"focus": "x"}, "artist-9")
    )
    assert result == {"error": "unknown_tool", "tool": "schedule_coaching_session"}
    assert not_connected is False
