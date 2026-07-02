"""
PROOF tests — Quinn (pr-agent) Anthropic tool_use loop, wired to REAL pr_service.

Mirrors tests/test_wire_lex_cipher.py. Proves that, in /api/chat_stream:
  (a) Quinn emits list_pr_contacts -> log_pr_outreach -> send_pr_pitch then a
      final message; the REAL pr_service DB functions are invoked and the stream
      surfaces a populated `actions` event with PR_AGENT_TOOLS on every create();
  (b) a non-target agent never receives PR_AGENT_TOOLS;
  (c) the gate is exclusive (Marcus still uses MARCUS_TOOLS);
  (d) an unconnected Gmail account degrades the send gracefully;
  (e) expired auth degrades the same way.

Zero network / LLM — the Anthropic client is faked; pr_service functions run
against the per-test temp SQLite DB (DB_PATH) via recording wrappers over the
REAL functions.
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


def test_pr_agent_tool_loop_invokes_real_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("PR_GMAIL_CONNECTED", "true")

    list_calls, create_rows = [], []
    real_list   = m.pr_service._db_list_pr_contacts
    real_create = m.pr_service._db_create_pr_outreach

    def rec_list(genre="", tier="", outlet_type=""):
        list_calls.append({"genre": genre, "tier": tier, "outlet_type": outlet_type})
        return real_list(genre=genre, tier=tier, outlet_type=outlet_type)

    def rec_create(o):
        create_rows.append(dict(o))
        return real_create(o)

    monkeypatch.setattr(m.pr_service, "_db_list_pr_contacts", rec_list)
    monkeypatch.setattr(m.pr_service, "_db_create_pr_outreach", rec_create)

    responses = [
        _Resp([_Block("tool_use", name="list_pr_contacts",
                      input={"genre": "indie", "tier": "A"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="log_pr_outreach",
                      input={"contact_id": "c-1", "subject": "Premiere?", "body": "Hi"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="send_pr_pitch",
                      input={"contact_id": "c-1", "subject": "Premiere?"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — searched contacts, logged and queued the pitch.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Quinn must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "pr-agent",
        "message":   "find press contacts and pitch them",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert list_calls == [{"genre": "indie", "tier": "A", "outlet_type": ""}], list_calls
    # Two REAL outreach rows written: the draft log and the queued send.
    assert [r["status"] for r in create_rows] == ["draft", "queued"], create_rows
    assert all(r["artist_id"] == "artist-9" and r["contact_id"] == "c-1" for r in create_rows)

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["list_pr_contacts", "log_pr_outreach", "send_pr_pitch"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "contact(s) found" in by_tool["list_pr_contacts"]["result"]
    assert by_tool["log_pr_outreach"]["result"] == "outreach logged"
    assert by_tool["send_pr_pitch"]["result"] == "pitch queued"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 4
    assert all(kw.get("tools") == m.PR_AGENT_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_pr_agent_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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


def test_pr_agent_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.PR_AGENT_TOOLS


def test_pr_agent_gmail_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("PR_GMAIL_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="send_pr_pitch",
                      input={"contact_id": "c-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Connect Gmail first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "pr-agent",
        "message":   "send the pitch",
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


def test_pr_agent_gmail_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("PR_GMAIL_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="send_pr_pitch",
                      input={"contact_id": "c-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Gmail auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "pr-agent",
        "message":   "send the pitch",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "auth_expired"
