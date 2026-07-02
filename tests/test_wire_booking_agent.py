"""
PROOF tests — Avery (booking-agent) tool_use loop, wired to REAL booking_service.

Mirrors tests/test_wire_pr_agent.py. Proves list_booking_contacts ->
log_booking_inquiry -> send_booking_inquiry, exclusive gating, and graceful
handling of an unconnected / expired Gmail account. Zero network / LLM — the
Anthropic client is faked; booking_service runs against the per-test temp DB.
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


def test_booking_agent_tool_loop_invokes_real_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("BOOKING_GMAIL_CONNECTED", "true")

    list_calls, create_rows = [], []
    real_list   = m.booking_service._db_list_booking_contacts
    real_create = m.booking_service._db_create_booking_inquiry

    def rec_list(genre="", tier="", city=""):
        list_calls.append({"genre": genre, "tier": tier, "city": city})
        return real_list(genre=genre, tier=tier, city=city)

    def rec_create(o):
        create_rows.append(dict(o))
        return real_create(o)

    monkeypatch.setattr(m.booking_service, "_db_list_booking_contacts", rec_list)
    monkeypatch.setattr(m.booking_service, "_db_create_booking_inquiry", rec_create)

    responses = [
        _Resp([_Block("tool_use", name="list_booking_contacts",
                      input={"genre": "indie", "tier": "A"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="log_booking_inquiry",
                      input={"contact_id": "b-1", "subject": "Spring tour?", "body": "Hi"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="send_booking_inquiry",
                      input={"contact_id": "b-1", "subject": "Spring tour?"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — searched venues, logged and queued the inquiry.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Avery must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "booking-agent",
        "message":   "find promoters and pitch a tour",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert list_calls == [{"genre": "indie", "tier": "A", "city": ""}], list_calls
    assert [r["status"] for r in create_rows] == ["draft", "queued"], create_rows
    assert all(r["artist_id"] == "artist-9" and r["contact_id"] == "b-1" for r in create_rows)

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["list_booking_contacts", "log_booking_inquiry", "send_booking_inquiry"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "contact(s) found" in by_tool["list_booking_contacts"]["result"]
    assert by_tool["log_booking_inquiry"]["result"] == "inquiry logged"
    assert by_tool["send_booking_inquiry"]["result"] == "inquiry queued"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 4
    assert all(kw.get("tools") == m.BOOKING_AGENT_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_booking_agent_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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
        "message":   "general check-in",
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


def test_booking_agent_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
        "message":   "next move",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    assert len(create_calls) == 1
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.BOOKING_AGENT_TOOLS


def test_booking_agent_gmail_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("BOOKING_GMAIL_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="send_booking_inquiry",
                      input={"contact_id": "b-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Connect Gmail first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "booking-agent",
        "message":   "send the inquiry",
        "artist_id": "artist-none",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]
    assert "done" in types and "error" not in types
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "not_connected"


def test_booking_agent_gmail_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("BOOKING_GMAIL_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="send_booking_inquiry",
                      input={"contact_id": "b-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Gmail auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "booking-agent",
        "message":   "send the inquiry",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "auth_expired"
