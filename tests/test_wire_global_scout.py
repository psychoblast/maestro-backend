"""
PROOF tests — Nova (global-scout) Anthropic tool_use loop.

Mirrors tests/test_wire_venue_hawk.py / tests/test_marcus_tool_use.py. Proves that,
in /api/chat_stream:

  (a) Nova emits search_markets -> draft_market_entry_plan then a final message;
      both mock-first global_scout_service functions are invoked with the correct
      args and the stream surfaces a populated `actions` event (actions_taken), with
      GLOBAL_SCOUT_TOOLS passed on every create() call;
  (b) a NON-scout agent (producer-connect) never receives GLOBAL_SCOUT_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never GLOBAL_SCOUT_TOOLS;
  (d) Nova is consult-only — the retired submit_distribution_registration
      mock-action tool (and its GLOBAL_SCOUT_ACCOUNT_CONNECTED gate) is gone from
      both the schema and the dispatch: it is neither offered to the model nor
      executable by name, and not_connected is structurally always False.

Everything is in-process and deterministic. NO network / LLM / distribution calls —
the Anthropic client is faked and the global_scout_service boundary is exercised
through recording wrappers over the REAL (pure, mock-first) functions.
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
    """Stand-in for async_client.messages.stream(...) — used by the non-scout path."""
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


# ── (a) Nova runs the tool loop and surfaces actions_taken ───────────────────

def test_scout_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    search_calls, draft_calls = [], []
    real_search = m.global_scout_service.search_markets
    real_draft  = m.global_scout_service.draft_market_entry_plan

    async def rec_search(genre="", region=""):
        search_calls.append({"genre": genre, "region": region})
        return await real_search(genre=genre, region=region)

    async def rec_draft(artist_id, market_id="", genre="", marketing_budget=0):
        draft_calls.append({"artist_id": artist_id, "market_id": market_id,
                            "genre": genre, "marketing_budget": marketing_budget})
        return await real_draft(artist_id, market_id=market_id,
                                genre=genre, marketing_budget=marketing_budget)

    monkeypatch.setattr(m.global_scout_service, "search_markets",          rec_search)
    monkeypatch.setattr(m.global_scout_service, "draft_market_entry_plan", rec_draft)

    responses = [
        _Resp([_Block("tool_use", name="search_markets",
                      input={"genre": "indie", "region": "Europe"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_market_entry_plan",
                      input={"market_id": "mkt-uk", "genre": "indie",
                             "marketing_budget": 5000}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — I mapped the market and drafted the plan.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("global-scout must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "global-scout",
        "message":   "find where my indie sound works in Europe",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert search_calls == [{"genre": "indie", "region": "Europe"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "market_id": "mkt-uk",
        "genre": "indie", "marketing_budget": 5000,
    }], draft_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_markets", "draft_market_entry_plan"], tools_used
    assert actions_evt["global_distribution_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "market(s) found" in by_tool["search_markets"]["result"]
    assert "viable=True" in by_tool["draft_market_entry_plan"]["result"]
    assert "enter" in by_tool["draft_market_entry_plan"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.GLOBAL_SCOUT_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VENUE_HAWK_TOOLS for kw in create_calls)


# ── (b) Non-scout agent never gets scout tools, takes the unchanged path ──────

def test_non_scout_agent_never_receives_scout_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT global-scout, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert create_calls == [], "non-scout agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not scout tools ─────

def test_marcus_still_uses_marcus_tools_not_scout(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.GLOBAL_SCOUT_TOOLS


# ── (d) Nova's tool roster is consult-only; the retired mock tool cannot reappear ──

def test_global_scout_tool_roster_is_consult_only(monkeypatch, tmp_path):
    """This unit owns Nova's exact tool roster: exactly the two consult tools,
    nothing more. The retired submit_distribution_registration mock-action tool
    must not reappear."""
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.GLOBAL_SCOUT_TOOLS]
    assert names == ["search_markets", "draft_market_entry_plan"], names
    assert "submit_distribution_registration" not in names
    assert not hasattr(m.global_scout_service, "submit_distribution_registration")
    assert not hasattr(m.global_scout_service, "GlobalDistributionNotConnected")
    assert not hasattr(m.global_scout_service, "GlobalDistributionAuthExpired")


def test_global_scout_unknown_tool_name_is_handled_gracefully(monkeypatch, tmp_path):
    """A retired/unknown tool name must degrade to the unknown_tool branch, not crash."""
    m = _load_main(monkeypatch, tmp_path)
    import asyncio
    result, summary, not_connected = asyncio.run(
        m._execute_global_scout_tool("submit_distribution_registration",
                                      {"market_id": "mkt-uk"}, "artist-9")
    )
    assert result == {"error": "unknown_tool", "tool": "submit_distribution_registration"}
    assert not_connected is False
