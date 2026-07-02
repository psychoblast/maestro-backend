"""
PROOF tests — Mo (mobile-monetize) Anthropic tool_use loop.

Mirrors tests/test_wire_lex_cipher.py / test_wire_ai_navigator.py. Proves that,
in /api/chat_stream: (a) Mo emits search_monetization_programs -> analyze_monetization -> enable_monetization then a final message
and surfaces a populated `actions` event with MOBILE_MONETIZE_TOOLS on every create();
(b) a non-target agent never receives MOBILE_MONETIZE_TOOLS; (c) the gate is exclusive
(Marcus still uses MARCUS_TOOLS); (d) the not-connected path is graceful; and
(e) expired auth degrades the same way. Zero network / LLM — the Anthropic client
is faked and the mobile_monetize_service boundary is exercised through recording wrappers over
the REAL (pure, mock-first) functions.
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


def test_mobile_monetize_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("MOBILE_MONETIZE_CONNECTED", "true")

    f1_calls, f2_calls, f3_calls = [], [], []
    real_f1 = m.mobile_monetize_service.search_monetization_programs
    real_f2 = m.mobile_monetize_service.analyze_monetization
    real_f3 = m.mobile_monetize_service.enable_monetization

    async def rec_f1(platform="", tier=""):
        f1_calls.append({"platform": platform, "tier": tier})
        return await real_f1(platform=platform, tier=tier)

    async def rec_f2(artist_id, metrics_text="", context=""):
        f2_calls.append({"artist_id": artist_id, "metrics_text": metrics_text, "context": context})
        return await real_f2(artist_id, metrics_text=metrics_text, context=context)

    async def rec_f3(artist_id, platform, program="ads"):
        f3_calls.append({"artist_id": artist_id, "platform": platform, "program": program})
        return await real_f3(artist_id, platform, program)

    monkeypatch.setattr(m.mobile_monetize_service, "search_monetization_programs", rec_f1)
    monkeypatch.setattr(m.mobile_monetize_service, "analyze_monetization", rec_f2)
    monkeypatch.setattr(m.mobile_monetize_service, "enable_monetization", rec_f3)

    responses = [
        _Resp([_Block("tool_use", name="search_monetization_programs", input={"platform": "youtube"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="analyze_monetization",
                      input={"metrics_text": "under 1000 subs", "context": "ctx"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="enable_monetization",
                      input={"platform": "Test Item", "program": "ads"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — took the actions across all three tools.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Mo must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "mobile-monetize",
        "message":   "take some actions for me",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert f1_calls == [{"platform": "youtube", "tier": ""}], f1_calls
    assert f2_calls == [{"artist_id": "artist-9", "metrics_text": "under 1000 subs", "context": "ctx"}], f2_calls
    assert f3_calls == [{"artist_id": "artist-9", "platform": "Test Item", "program": "ads"}], f3_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_monetization_programs", "analyze_monetization", "enable_monetization"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "program(s) found" in by_tool["search_monetization_programs"]["result"]
    assert "blocker(s)" in by_tool["analyze_monetization"]["result"]
    assert by_tool["enable_monetization"]["result"] == "monetization enabled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 4
    assert all(kw.get("tools") == m.MOBILE_MONETIZE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_mobile_monetize_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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


def test_mobile_monetize_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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


def test_mobile_monetize_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("MOBILE_MONETIZE_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="enable_monetization", input={"platform": "Blocked Item"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect an account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "mobile-monetize",
        "message":   "do the gated action",
        "artist_id": "artist-none",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert "done" in types
    assert "error" not in types, types
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "not_connected"


def test_mobile_monetize_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("MOBILE_MONETIZE_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="enable_monetization", input={"platform": "Old Item"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "mobile-monetize",
        "message":   "do the gated action on the old item",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "auth_expired"
