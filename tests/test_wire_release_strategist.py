"""
PROOF tests — Sage (release-strategist) tool_use loop, wired to REAL release_service.

Mirrors tests/test_wire_pr_agent.py. Proves list_releases -> create_release ->
schedule_campaign (which persists the REAL _build_campaign_actions plan),
exclusive gating, and graceful handling of missing / expired campaign automation.
Zero network / LLM — the Anthropic client is faked; release_service runs against
the per-test temp DB.
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


def test_release_strategist_tool_loop_invokes_real_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("RELEASE_AUTOMATION_CONNECTED", "true")

    list_calls, release_rows, action_rows = [], [], []
    real_list   = m.release_service._db_list_releases
    real_create = m.release_service._db_create_release
    real_action = m.release_service._db_create_action

    def rec_list(artist_id):
        list_calls.append(artist_id)
        return real_list(artist_id)

    def rec_create(r):
        release_rows.append(dict(r))
        return real_create(r)

    def rec_action(a):
        action_rows.append(dict(a))
        return real_action(a)

    monkeypatch.setattr(m.release_service, "_db_list_releases", rec_list)
    monkeypatch.setattr(m.release_service, "_db_create_release", rec_create)
    monkeypatch.setattr(m.release_service, "_db_create_action", rec_action)
    # Stored release for the scheduler to plan against (valid YYYY-MM-DD).
    monkeypatch.setattr(m.release_service, "_db_get_release", lambda rid: {
        "id": rid, "artist_id": "artist-9", "title": "Debut LP",
        "release_date": "2026-09-01", "genre": "indie", "mood": "warm",
    })

    responses = [
        _Resp([_Block("tool_use", name="list_releases", input={}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="create_release",
                      input={"title": "Debut LP", "release_date": "2026-09-01", "genre": "indie"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_campaign",
                      input={"release_id": "rel-x"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — listed releases, created the LP and scheduled the campaign.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Sage must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "release-strategist",
        "message":   "plan my album rollout",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert list_calls == ["artist-9"], list_calls
    assert len(release_rows) == 1 and release_rows[0]["status"] == "draft"
    assert release_rows[0]["title"] == "Debut LP" and release_rows[0]["artist_id"] == "artist-9"
    # The REAL _build_campaign_actions plan was persisted (one row per wave).
    assert len(action_rows) >= 1
    assert all(a["release_id"] == "rel-x" for a in action_rows)

    assert "actions" in types and "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["list_releases", "create_release", "schedule_campaign"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "release(s) found" in by_tool["list_releases"]["result"]
    assert by_tool["create_release"]["result"] == "release created"
    assert by_tool["schedule_campaign"]["result"] == "campaign scheduled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 4
    assert all(kw.get("tools") == m.RELEASE_STRATEGIST_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_release_strategist_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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


def test_release_strategist_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.RELEASE_STRATEGIST_TOOLS


def test_release_strategist_automation_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("RELEASE_AUTOMATION_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="schedule_campaign",
                      input={"release_id": "rel-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Connect automation first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "release-strategist",
        "message":   "schedule the campaign",
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


def test_release_strategist_automation_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("RELEASE_AUTOMATION_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="schedule_campaign",
                      input={"release_id": "rel-9"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Automation auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "release-strategist",
        "message":   "schedule the campaign",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "auth_expired"
