"""
PROOF tests — Tommy (label-services) Anthropic tool_use loop.

Mirrors tests/test_wire_lex_cipher.py / test_wire_ai_navigator.py. Proves that,
in /api/chat_stream: (a) Tommy emits search_distribution_requirements -> validate_release_metadata -> deliver_to_dsps then a final message
and surfaces a populated `actions` event with LABEL_SERVICES_TOOLS on every create();
(b) a non-target agent never receives LABEL_SERVICES_TOOLS; (c) the gate is exclusive
(Marcus still uses MARCUS_TOOLS); (d) the not-connected path is graceful; and
(e) expired auth degrades the same way. Zero network / LLM — the Anthropic client
is faked and the label_services_service boundary is exercised through recording wrappers over
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


def test_label_services_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("LABEL_SERVICES_CONNECTED", "true")

    f1_calls, f2_calls, f3_calls = [], [], []
    real_f1 = m.label_services_service.search_distribution_requirements
    real_f2 = m.label_services_service.validate_release_metadata
    real_f3 = m.label_services_service.deliver_to_dsps

    async def rec_f1(store="", asset_type=""):
        f1_calls.append({"store": store, "asset_type": asset_type})
        return await real_f1(store=store, asset_type=asset_type)

    async def rec_f2(artist_id, metadata_text="", context=""):
        f2_calls.append({"artist_id": artist_id, "metadata_text": metadata_text, "context": context})
        return await real_f2(artist_id, metadata_text=metadata_text, context=context)

    async def rec_f3(artist_id, release_title, store="all"):
        f3_calls.append({"artist_id": artist_id, "release_title": release_title, "store": store})
        return await real_f3(artist_id, release_title, store)

    monkeypatch.setattr(m.label_services_service, "search_distribution_requirements", rec_f1)
    monkeypatch.setattr(m.label_services_service, "validate_release_metadata", rec_f2)
    monkeypatch.setattr(m.label_services_service, "deliver_to_dsps", rec_f3)

    responses = [
        _Resp([_Block("tool_use", name="search_distribution_requirements", input={"store": "spotify"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="validate_release_metadata",
                      input={"metadata_text": "no isrc", "context": "ctx"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="deliver_to_dsps",
                      input={"release_title": "Test Item", "store": "all"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — took the actions across all three tools.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("Tommy must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "label-services",
        "message":   "take some actions for me",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert f1_calls == [{"store": "spotify", "asset_type": ""}], f1_calls
    assert f2_calls == [{"artist_id": "artist-9", "metadata_text": "no isrc", "context": "ctx"}], f2_calls
    assert f3_calls == [{"artist_id": "artist-9", "release_title": "Test Item", "store": "all"}], f3_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_distribution_requirements", "validate_release_metadata", "deliver_to_dsps"], tools_used
    assert actions_evt["not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "requirement(s) found" in by_tool["search_distribution_requirements"]["result"]
    assert "issue(s)" in by_tool["validate_release_metadata"]["result"]
    assert by_tool["deliver_to_dsps"]["result"] == "delivery queued"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 4
    assert all(kw.get("tools") == m.LABEL_SERVICES_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)


def test_label_services_non_target_agent_never_receives_tools(monkeypatch, tmp_path):
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


def test_label_services_marcus_still_uses_marcus_tools(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.LABEL_SERVICES_TOOLS


def test_label_services_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.delenv("LABEL_SERVICES_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="deliver_to_dsps", input={"release_title": "Blocked Item"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect an account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "label-services",
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


def test_label_services_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    monkeypatch.setenv("LABEL_SERVICES_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="deliver_to_dsps", input={"release_title": "Old Item"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "label-services",
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
