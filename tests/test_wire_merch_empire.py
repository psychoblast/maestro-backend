"""
PROOF tests — Max (merch-empire) Anthropic tool_use loop.

Mirrors tests/test_wire_brand_connect.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Max emits search_merch_products -> build_production_run then a final message;
      both mock-first merch_empire_service functions are invoked with the correct
      args and the stream surfaces a populated `actions` event (actions_taken), with
      MERCH_EMPIRE_TOOLS passed on every create() call;
  (b) a NON-merch-empire agent (producer-connect) never receives MERCH_EMPIRE_TOOLS — it
      takes the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never MERCH_EMPIRE_TOOLS;
  (d) Max is consult-only — the retired schedule_fulfillment_order mock-action tool
      (and its MERCH_EMPIRE_ACCOUNT_CONNECTED gate) is gone from both the schema and
      the dispatch: it is neither offered to the model nor executable by name, and
      not_connected is structurally always False.

Everything is in-process and deterministic. NO network / LLM / fulfilment calls —
the Anthropic client is faked and the merch_empire_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-merch-empire path."""
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


# ── (a) Max runs the tool loop and surfaces actions_taken ────────────────────

def test_merch_empire_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    search_calls, build_calls = [], []
    real_search = m.merch_empire_service.search_merch_products
    real_build  = m.merch_empire_service.build_production_run

    async def rec_search(category="", tier=""):
        search_calls.append({"category": category, "tier": tier})
        return await real_search(category=category, tier=tier)

    async def rec_build(artist_id, product_id="", design_name="", quantity=0):
        build_calls.append({"artist_id": artist_id, "product_id": product_id,
                            "design_name": design_name, "quantity": quantity})
        return await real_build(artist_id, product_id=product_id,
                                design_name=design_name, quantity=quantity)

    monkeypatch.setattr(m.merch_empire_service, "search_merch_products", rec_search)
    monkeypatch.setattr(m.merch_empire_service, "build_production_run",  rec_build)

    responses = [
        _Resp([_Block("tool_use", name="search_merch_products",
                      input={"category": "apparel", "tier": "starter"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_production_run",
                      input={"product_id": "merch-classic-tee",
                             "design_name": "tour-2026",
                             "quantity": 100}, id="t2")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the product and costed the run.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("merch-empire must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "merch-empire",
        "message":   "cost a starter apparel run for my tour",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert search_calls == [{"category": "apparel", "tier": "starter"}], search_calls
    assert build_calls == [{
        "artist_id": "artist-9", "product_id": "merch-classic-tee",
        "design_name": "tour-2026", "quantity": 100,
    }], build_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == ["search_merch_products", "build_production_run"], tools_used
    assert actions_evt["fulfillment_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "product(s) found" in by_tool["search_merch_products"]["result"]
    assert "viable=True" in by_tool["build_production_run"]["result"]
    assert "produce" in by_tool["build_production_run"]["result"]

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    assert len(create_calls) == 3
    assert all(kw.get("tools") == m.MERCH_EMPIRE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.BRAND_CONNECT_TOOLS for kw in create_calls)


# ── (b) Non-merch-empire agent never gets merch tools, unchanged path ─────────

def test_non_merch_empire_agent_never_receives_merch_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT merch-empire, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert create_calls == [], "non-merch-empire agent must not invoke the tool_use create loop"
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not merch tools ─────

def test_marcus_still_uses_marcus_tools_not_merch_empire(monkeypatch, tmp_path):
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
    assert create_calls[0].get("tools") != m.MERCH_EMPIRE_TOOLS


# ── (d) Max's tool roster is consult-only; the retired mock tool cannot reappear ──

def test_merch_empire_tool_roster_is_consult_only(monkeypatch, tmp_path):
    """This unit owns Max's exact tool roster: exactly the two consult tools,
    nothing more. The retired schedule_fulfillment_order mock-action tool must not
    reappear."""
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.MERCH_EMPIRE_TOOLS]
    assert names == ["search_merch_products", "build_production_run"], names
    assert "schedule_fulfillment_order" not in names
    assert not hasattr(m.merch_empire_service, "schedule_fulfillment_order")
    assert not hasattr(m.merch_empire_service, "MerchAccountNotConnected")
    assert not hasattr(m.merch_empire_service, "MerchAccountAuthExpired")


def test_merch_empire_unknown_tool_name_is_handled_gracefully(monkeypatch, tmp_path):
    """A retired/unknown tool name must degrade to the unknown_tool branch, not crash."""
    m = _load_main(monkeypatch, tmp_path)
    import asyncio
    result, summary, not_connected = asyncio.run(
        m._execute_merch_empire_tool("schedule_fulfillment_order",
                                      {"product_id": "merch-classic-tee", "quantity": 10}, "artist-9")
    )
    assert result == {"error": "unknown_tool", "tool": "schedule_fulfillment_order"}
    assert not_connected is False
