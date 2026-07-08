"""
PROOF tests — Reel (video-director) Anthropic tool_use loop.

Mirrors tests/test_wire_lex_cipher.py. Proves that, in /api/chat_stream:
(a) Reel emits search_directors -> estimate_video_budget then a final message
and surfaces a populated `actions` event with VIDEO_DIRECTOR_TOOLS on every create();
(b) a non-target agent never receives VIDEO_DIRECTOR_TOOLS; (c) the gate is exclusive
(Marcus still uses MARCUS_TOOLS); (d) Reel is consult-only — the retired
book_video_shoot mock-action tool (and its VIDEO_DIRECTOR_CONNECTED gate) is gone
from both the schema and the dispatch: it is neither offered to the model nor
executable by name, and not_connected is structurally always False.
Zero network / LLM — the Anthropic client is faked and the video_director_service
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


def test_video_director_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    f1_calls, f2_calls = [], []
    real_f1 = m.video_director_service.search_directors
    real_f2 = m.video_director_service.estimate_video_budget

    async def rec_f1(style="", budget_tier=""):
        f1_calls.append({"style": style, "budget_tier": budget_tier})
        return await real_f1(style=style, budget_tier=budget_tier)

    async def rec_f2(artist_id, treatment_notes="", context=""):
        f2_calls.append({"artist_id": artist_id, "treatment_notes": treatment_notes, "context": context})
        return await real_f2(artist_id, treatment_notes=treatment_notes, context=context)

    monkeypatch.setattr(m.video_director_service, "search_directors", rec_f1)
    monkeypatch.setattr(m.video_director_service, "estimate_video_budget", rec_f2)

    responses = [
        _Resp([_Block("tool_use", name="search_directors", input={"style": "narrative"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="estimate_video_budget",
                      input={"treatment_notes": "multiple locations", "context": "ctx"}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — took the actions across both tools.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Reel must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "video-director",
        "message":   "take some actions for me",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert f1_calls == [{"style": "narrative", "budget_tier": ""}], f1_calls
    assert f2_calls == [{"artist_id": "artist-9", "treatment_notes": "multiple locations", "context": "ctx"}], f2_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_directors", "estimate_video_budget"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "director(s) found" in by_tool["search_directors"]["result"]
    assert "cost driver(s)" in by_tool["estimate_video_budget"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.VIDEO_DIRECTOR_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_video_director_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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


def test_video_director_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.VIDEO_DIRECTOR_TOOLS


def test_video_director_tool_roster_is_consult_only(monkeypatch, tmp_path):
    """This unit owns Reel's exact tool roster: exactly the two consult tools,
    nothing more. The retired book_video_shoot mock-action tool must not reappear."""
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.VIDEO_DIRECTOR_TOOLS]
    assert names == ["search_directors", "estimate_video_budget"], names
    assert "book_video_shoot" not in names
    assert not hasattr(m.video_director_service, "book_video_shoot")
    assert not hasattr(m.video_director_service, "ProductionAccountNotConnected")
    assert not hasattr(m.video_director_service, "ProductionAccountAuthExpired")


def test_video_director_unknown_tool_name_is_handled_gracefully(monkeypatch, tmp_path):
    """A retired/unknown tool name must degrade to the unknown_tool branch, not crash."""
    m = _load_main(monkeypatch, tmp_path)
    import asyncio
    result, summary, not_connected = asyncio.run(
        m._execute_video_director_tool("book_video_shoot", {"project_title": "x"}, "artist-9")
    )
    assert result == {"error": "unknown_tool", "tool": "book_video_shoot"}
    assert not_connected is False
