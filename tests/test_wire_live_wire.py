"""
PROOF tests — Knox (live-wire) Anthropic tool_use loop.

NOTE (RAY-B build, July 2026): Knox's search_venues and submit_booking_hold were
DUPLICATES of Ray B's booking tools and were REMOVED — Ray B / venue-hawk OWNS
booking (see _audit/rayb_step0_collision_report.md). Knox keeps ONLY its own,
non-duplicate assess_show_offer screen, which is ungated.

Mirrors tests/test_wire_lex_cipher.py. Proves that, in /api/chat_stream:
(a) Knox emits assess_show_offer then a final message and surfaces a populated
`actions` event with LIVE_WIRE_TOOLS on every create();
(b) a non-target agent never receives LIVE_WIRE_TOOLS;
(c) the gate is exclusive (Marcus still uses MARCUS_TOOLS); and
(d) the duplicate booking tools are gone from both the schema and the service.
Zero network / LLM — the Anthropic client is faked and the live_wire_service
boundary is exercised through recording wrappers over the REAL functions.
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


def test_live_wire_tool_loop_invokes_function_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    f_calls = []
    real_assess = m.live_wire_service.assess_show_offer

    async def rec_assess(artist_id, offer_text="", context=""):
        f_calls.append({"artist_id": artist_id, "offer_text": offer_text, "context": context})
        return await real_assess(artist_id, offer_text=offer_text, context=context)

    monkeypatch.setattr(m.live_wire_service, "assess_show_offer", rec_assess)

    responses = [
        _Resp([_Block("tool_use", name="assess_show_offer",
                      input={"offer_text": "no guarantee", "context": "ctx"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Done — screened the offer.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Knox must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "live-wire",
        "message":   "screen this offer for me",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert f_calls == [{"artist_id": "artist-9", "offer_text": "no guarantee", "context": "ctx"}], f_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["assess_show_offer"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "issue(s)" in by_tool["assess_show_offer"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 2
    assert all(kw.get("tools") == m.LIVE_WIRE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_live_wire_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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


def test_live_wire_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.LIVE_WIRE_TOOLS


def test_live_wire_duplicate_booking_tools_removed(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    # Schema: only assess_show_offer remains on Knox.
    names = [t["name"] for t in m.LIVE_WIRE_TOOLS]
    assert names == ["assess_show_offer"], names
    # Service: the duplicated booking functions and their gate/exceptions are gone.
    assert not hasattr(m.live_wire_service, "search_venues")
    assert not hasattr(m.live_wire_service, "submit_booking_hold")
    assert not hasattr(m.live_wire_service, "BookingAccountNotConnected")
    assert not hasattr(m.live_wire_service, "BookingAccountAuthExpired")
