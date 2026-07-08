"""
PROOF tests — Beat (producer-connect) Anthropic tool_use loop.

Mirrors tests/test_wire_ar_scout.py / tests/test_marcus_tool_use.py. Proves that,
in /api/chat_stream:

  (a) Beat emits search_producers -> evaluate_beat_deal then a final message; both
      mock-first producer_connect_service functions are invoked with the correct
      args and the stream surfaces a populated `actions` event (actions_taken),
      with PRODUCER_CONNECT_TOOLS passed on every create() call;
  (b) a NON-producer-connect agent (collab-connect) never receives
      PRODUCER_CONNECT_TOOLS — it takes the unchanged streaming path and emits NO
      `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never PRODUCER_CONNECT_TOOLS;
  (d) Beat is consult-only — the retired log_collab_request mock-action tool (and
      its PRODUCER_NETWORK_CONNECTED gate) is gone from both the schema and the
      dispatch: it is neither offered to the model nor executable by name, and
      not_connected is structurally always False.

Everything is in-process and deterministic. NO network / LLM / production-network
calls — the Anthropic client is faked and the producer_connect_service boundary is
exercised through recording wrappers over the REAL (pure, mock-first) functions.
"""
import importlib
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


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
    """Stand-in for async_client.messages.stream(...) — used by the non-beat path."""
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


# ── (a) Beat runs the tool loop and surfaces actions_taken ───────────────────

def test_producer_connect_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    search_calls, eval_calls = [], []
    real_search = m.producer_connect_service.search_producers
    real_eval   = m.producer_connect_service.evaluate_beat_deal

    async def rec_search(genre="", region="", tier=""):
        search_calls.append({"genre": genre, "region": region, "tier": tier})
        return await real_search(genre=genre, region=region, tier=tier)

    async def rec_eval(artist_id, beat_title="", license_type="", price_usd=0):
        eval_calls.append({"artist_id": artist_id, "beat_title": beat_title,
                           "license_type": license_type, "price_usd": price_usd})
        return await real_eval(artist_id, beat_title=beat_title,
                               license_type=license_type, price_usd=price_usd)

    monkeypatch.setattr(m.producer_connect_service, "search_producers",  rec_search)
    monkeypatch.setattr(m.producer_connect_service, "evaluate_beat_deal", rec_eval)

    responses = [
        _Resp([_Block("tool_use", name="search_producers",
                      input={"genre": "hip hop", "tier": "mid"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="evaluate_beat_deal",
                      input={"beat_title": "Skyline", "license_type": "exclusive",
                             "price_usd": 2500}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the producer and scored the deal.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("producer-connect must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "producer-connect",
        "message":   "find a mid-tier hip hop producer and score a beat deal",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert search_calls == [{"genre": "hip hop", "region": "", "tier": "mid"}], search_calls
    assert eval_calls == [{
        "artist_id": "artist-9", "beat_title": "Skyline",
        "license_type": "exclusive", "price_usd": 2500,
    }], eval_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_producers", "evaluate_beat_deal"], tools_used
    assert actions_evt["producer_network_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "producer(s) found" in by_tool["search_producers"]["result"]
    assert "composite=" in by_tool["evaluate_beat_deal"]["result"]
    assert any(rec in by_tool["evaluate_beat_deal"]["result"]
               for rec in ("accept", "negotiate", "pass")), by_tool["evaluate_beat_deal"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.PRODUCER_CONNECT_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.AR_SCOUT_TOOLS for kw in create_calls)


# ── (b) Non-beat agent never gets beat tools, takes the unchanged path ────────

def test_non_producer_connect_agent_never_receives_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT producer-connect, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert create_calls == [], "non-beat agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not beat tools ──────

def test_marcus_still_uses_marcus_tools_not_producer_connect(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.PRODUCER_CONNECT_TOOLS


# ── (d) Beat's tool roster is consult-only; the retired mock tool cannot reappear ──

def test_producer_connect_tool_roster_is_consult_only(monkeypatch, tmp_path):
    """This unit owns Beat's exact tool roster: exactly the two consult tools,
    nothing more. The retired log_collab_request mock-action tool must not
    reappear."""
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.PRODUCER_CONNECT_TOOLS]
    assert names == ["search_producers", "evaluate_beat_deal"], names
    assert "log_collab_request" not in names
    assert not hasattr(m.producer_connect_service, "log_collab_request")
    assert not hasattr(m.producer_connect_service, "ProducerNetworkNotConnected")
    assert not hasattr(m.producer_connect_service, "ProducerNetworkAuthExpired")


def test_producer_connect_unknown_tool_name_is_handled_gracefully(monkeypatch, tmp_path):
    """A retired/unknown tool name must degrade to the unknown_tool branch, not crash."""
    m = _load_main(monkeypatch, tmp_path)
    import asyncio
    result, summary, not_connected = asyncio.run(
        m._execute_producer_connect_tool("log_collab_request", {"producer_id": "prd-tape-room"}, "artist-9")
    )
    assert result == {"error": "unknown_tool", "tool": "log_collab_request"}
    assert not_connected is False
