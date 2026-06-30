"""
Unit 1.7 PROOF tests — Marcus (puppet-master) Anthropic tool_use loop.

Prove that, in /api/chat_stream:

  (a) Marcus emits search_curators then send_pitch_email then a final message;
      both internal pitch_service functions are invoked with the correct args and
      the stream surfaces a populated `actions` event (actions_taken);
  (b) a NON-Marcus agent never receives `tools` — messages.create is never called,
      it takes the unchanged streaming path, and emits NO `actions` event;
  (c) the gmail_not_connected path is handled gracefully (no crash; the actions
      event carries gmail_not_connected=True).

Everything is in-process and deterministic. NO network / LLM / Gmail calls — the
Anthropic client is faked and every pitch_service boundary is monkeypatched.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Fake Anthropic SDK shapes ────────────────────────────────────────────────

class _Block:
    """Stand-in for an Anthropic content block (text or tool_use)."""
    def __init__(self, type, text=None, name=None, input=None, id=None):
        self.type  = type
        self.text  = text
        self.name  = name
        self.input = input
        self.id    = id


class _Resp:
    """Stand-in for a messages.create(...) response."""
    def __init__(self, content, stop_reason):
        self.content     = content
        self.stop_reason = stop_reason


class _FakeStream:
    """Stand-in for async_client.messages.stream(...) — used by the non-Marcus path."""
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


# ── (a) Marcus runs the tool loop and surfaces actions_taken ─────────────────

def test_marcus_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # Record calls into the existing pitch_service functions.
    list_calls, get_calls, send_calls = [], [], []

    def fake_list_curators(genre="", tier="", platform="", min_followers=0):
        list_calls.append({"genre": genre, "tier": tier})
        return [{
            "id": "cur-1", "name": "Test Curator", "outlet": "PlaylistX",
            "genres": ["indie", "pop"], "tier": "A", "contact_email": "c@example.com",
        }]

    def fake_get_curator(curator_id):
        get_calls.append(curator_id)
        return {"id": "cur-1", "name": "Test Curator", "contact_email": "c@example.com"}

    async def fake_send_email(artist_id, to, subject, body):
        send_calls.append({"artist_id": artist_id, "to": to, "subject": subject, "body": body})
        return {"message_id": "msg-123", "thread_id": "thr-1", "status": "sent"}

    monkeypatch.setattr(m.pitch_service, "_db_list_curators", fake_list_curators)
    monkeypatch.setattr(m.pitch_service, "_db_get_curator",   fake_get_curator)
    monkeypatch.setattr(m.pitch_service, "send_email",        fake_send_email)

    # Scripted Anthropic responses: search_curators → send_pitch_email → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_curators",
                      input={"genre": "indie pop"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="send_pitch_email",
                      input={"curator_id": "cur-1", "subject": "Sub", "body": "Body"},
                      id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — I found a curator and sent your pitch.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Marcus.
    def _no_stream(**kw):
        raise AssertionError("Marcus must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "puppet-master",
        "message":   "find indie pop curators and pitch my single",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Both internal functions invoked with correct args.
    assert list_calls == [{"genre": "indie pop", "tier": ""}], list_calls
    assert get_calls  == ["cur-1"], get_calls
    assert send_calls == [{
        "artist_id": "artist-9", "to": "c@example.com",
        "subject": "Sub", "body": "Body",
    }], send_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_curators", "send_pitch_email"], tools_used
    assert actions_evt["gmail_not_connected"] is False
    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Three create() round-trips: search, send, final.
    assert len(create_calls) == 3
    # Tools were passed on every Marcus create call.
    assert all(kw.get("tools") == m.MARCUS_TOOLS for kw in create_calls)


# ── (b) Non-Marcus agent never gets tools, takes the unchanged path ──────────

def test_non_marcus_agent_never_receives_tools(monkeypatch, tmp_path):
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
        "agent_id":  "ar-scout",   # NOT puppet-master
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: messages.create (the tool loop) is never touched.
    assert create_calls == [], "non-Marcus agent must not invoke the tool_use create loop"
    # No actions event for non-Marcus agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) gmail_not_connected handled gracefully ───────────────────────────────

def test_marcus_gmail_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setattr(m.pitch_service, "_db_get_curator",
                        lambda cid: {"id": cid, "name": "Test Curator",
                                     "contact_email": "c@example.com"})

    async def fake_send_email(artist_id, to, subject, body):
        raise m.pitch_service.GmailNotConnected("no tokens")

    monkeypatch.setattr(m.pitch_service, "send_email", fake_send_email)

    responses = [
        _Resp([_Block("tool_use", name="send_pitch_email",
                      input={"curator_id": "cur-1", "subject": "S", "body": "B"},
                      id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect Gmail first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "puppet-master",
        "message":   "pitch curator cur-1",
        "artist_id": "artist-no-gmail",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Stream completes without crashing.
    assert "done" in types
    assert "error" not in types, types
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["gmail_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "gmail_not_connected"


# ── (d) search_curators forwards platform + min_followers to _db_list_curators ─

def test_marcus_search_curators_forwards_platform_and_min_followers(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    list_calls = []

    def fake_list_curators(genre="", tier="", platform="", min_followers=0):
        list_calls.append({
            "genre": genre, "tier": tier,
            "platform": platform, "min_followers": min_followers,
        })
        return []

    monkeypatch.setattr(m.pitch_service, "_db_list_curators", fake_list_curators)

    responses = [
        _Resp([_Block("tool_use", name="search_curators",
                      input={"genre": "indie", "platform": "spotify",
                             "min_followers": 5000}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Here are the curators I found.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "puppet-master",
        "message":   "find indie spotify curators with at least 5000 followers",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200

    # platform + min_followers from tool_input reached _db_list_curators intact.
    assert list_calls == [{
        "genre": "indie", "tier": "",
        "platform": "spotify", "min_followers": 5000,
    }], list_calls
