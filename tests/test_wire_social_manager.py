"""
PROOF tests — Riley (social-manager) tool_use loop, wired to REAL social_service.

Mirrors tests/test_wire_pr_agent.py. Proves list_social_posts ->
draft_social_post -> schedule_post, exclusive gating, and graceful handling of a
missing / expired Buffer connection (social_service._load_buffer_tokens). Zero
network / LLM — the Anthropic client is faked; social_service runs against the
per-test temp DB.
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


def test_social_manager_tool_loop_invokes_real_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    list_calls, create_rows, update_calls = [], [], []
    real_list   = m.social_service._db_list_posts
    real_create = m.social_service._db_create_post
    real_update = m.social_service._db_update_post

    def rec_list(artist_id, platform="", status=""):
        list_calls.append({"artist_id": artist_id, "platform": platform, "status": status})
        return real_list(artist_id, platform=platform, status=status)

    def rec_create(p):
        create_rows.append(dict(p))
        return real_create(p)

    def rec_update(post_id, updates):
        update_calls.append({"post_id": post_id, "updates": dict(updates)})
        return real_update(post_id, updates)

    # Connected Buffer account (no network).
    monkeypatch.setattr(m.social_service, "_load_buffer_tokens", lambda artist_id: {"access_token": "x"})
    monkeypatch.setattr(m.social_service, "_db_list_posts", rec_list)
    monkeypatch.setattr(m.social_service, "_db_create_post", rec_create)
    monkeypatch.setattr(m.social_service, "_db_update_post", rec_update)

    responses = [
        _Resp([_Block("tool_use", name="list_social_posts",
                      input={"platform": "instagram"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_social_post",
                      input={"platform": "instagram", "content": "New single Friday"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_post",
                      input={"post_id": "p-1"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — listed posts, drafted and scheduled the new one.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Riley must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "social-manager",
        "message":   "draft and schedule a post",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert list_calls == [{"artist_id": "artist-9", "platform": "instagram", "status": ""}], list_calls
    assert len(create_rows) == 1 and create_rows[0]["status"] == "draft"
    assert create_rows[0]["artist_id"] == "artist-9" and create_rows[0]["platform"] == "instagram"
    assert update_calls == [{"post_id": "p-1", "updates": {"status": "scheduled"}}], update_calls

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["list_social_posts", "draft_social_post", "schedule_post"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "post(s) found" in by_tool["list_social_posts"]["result"]
    assert by_tool["draft_social_post"]["result"] == "post drafted"
    assert by_tool["schedule_post"]["result"] == "post scheduled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 4
    assert all(kw.get("tools") == m.SOCIAL_MANAGER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_social_manager_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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


def test_social_manager_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.SOCIAL_MANAGER_TOOLS


def test_social_manager_buffer_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    # No Buffer tokens → not connected.
    monkeypatch.setattr(m.social_service, "_load_buffer_tokens", lambda artist_id: {})

    responses = [
        _Resp([_Block("tool_use", name="schedule_post",
                      input={"post_id": "p-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Connect Buffer first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "social-manager",
        "message":   "schedule it",
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


def test_social_manager_buffer_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setattr(m.social_service, "_load_buffer_tokens", lambda artist_id: {"expired": True})

    responses = [
        _Resp([_Block("tool_use", name="schedule_post",
                      input={"post_id": "p-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Buffer auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "social-manager",
        "message":   "schedule it",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "auth_expired"
