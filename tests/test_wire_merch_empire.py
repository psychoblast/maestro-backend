"""
PROOF tests — Max (merch-empire) Anthropic tool_use loop.

Mirrors tests/test_wire_brand_connect.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Max emits search_merch_products → build_production_run →
      schedule_fulfillment_order then a final message; all three mock-first
      merch_empire_service functions are invoked with the correct args and the
      stream surfaces a populated `actions` event (actions_taken), with
      MERCH_EMPIRE_TOOLS passed on every create() call;
  (b) a NON-merch-empire agent (producer-connect) never receives MERCH_EMPIRE_TOOLS — it
      takes the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never MERCH_EMPIRE_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries fulfillment_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / fulfilment calls —
the Anthropic client is faked and the merch_empire_service boundary is exercised
through recording wrappers over the REAL (pure, mock-first) functions.
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

    # A connected print/fulfilment account so the order succeeds (no network).
    monkeypatch.setenv("MERCH_EMPIRE_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) merch_empire_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, build_calls, order_calls = [], [], []
    real_search = m.merch_empire_service.search_merch_products
    real_build  = m.merch_empire_service.build_production_run
    real_order  = m.merch_empire_service.schedule_fulfillment_order

    async def rec_search(category="", tier=""):
        search_calls.append({"category": category, "tier": tier})
        return await real_search(category=category, tier=tier)

    async def rec_build(artist_id, product_id="", design_name="", quantity=0):
        build_calls.append({"artist_id": artist_id, "product_id": product_id,
                            "design_name": design_name, "quantity": quantity})
        return await real_build(artist_id, product_id=product_id,
                                design_name=design_name, quantity=quantity)

    async def rec_order(artist_id, product_id, quantity=0, design_name=""):
        order_calls.append({"artist_id": artist_id, "product_id": product_id,
                            "quantity": quantity, "design_name": design_name})
        return await real_order(artist_id, product_id, quantity, design_name)

    monkeypatch.setattr(m.merch_empire_service, "search_merch_products",     rec_search)
    monkeypatch.setattr(m.merch_empire_service, "build_production_run",      rec_build)
    monkeypatch.setattr(m.merch_empire_service, "schedule_fulfillment_order", rec_order)

    # Scripted Anthropic responses: search → build → order → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_merch_products",
                      input={"category": "apparel", "tier": "starter"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_production_run",
                      input={"product_id": "merch-classic-tee",
                             "design_name": "tour-2026",
                             "quantity": 100}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_fulfillment_order",
                      input={"product_id": "merch-classic-tee",
                             "design_name": "tour-2026",
                             "quantity": 100}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the product, costed the run, and placed the order.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Max.
    def _no_stream(**kw):
        raise AssertionError("merch-empire must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "merch-empire",
        "message":   "produce a starter apparel run for my tour",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"category": "apparel", "tier": "starter"}], search_calls
    assert build_calls == [{
        "artist_id": "artist-9", "product_id": "merch-classic-tee",
        "design_name": "tour-2026", "quantity": 100,
    }], build_calls
    assert order_calls == [{
        "artist_id": "artist-9", "product_id": "merch-classic-tee",
        "quantity": 100, "design_name": "tour-2026",
    }], order_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_merch_products", "build_production_run", "schedule_fulfillment_order",
    ], tools_used
    assert actions_evt["fulfillment_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "product(s) found" in by_tool["search_merch_products"]["result"]
    # known product, present design + qty at/above min order → viable / produce.
    assert "viable=True" in by_tool["build_production_run"]["result"]
    assert "produce" in by_tool["build_production_run"]["result"]
    assert by_tool["schedule_fulfillment_order"]["result"] == "fulfilment order placed"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, build, order, final.
    assert len(create_calls) == 4
    # MERCH_EMPIRE_TOOLS passed on every merch-empire create call (never other toolsets).
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
        "agent_id":  "collab-connect",   # NOT merch-empire, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-merch-empire agent must not invoke the tool_use create loop"
    # No actions event for non-merch-empire agents.
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
    # Marcus keeps its own toolset — the merch-empire gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.MERCH_EMPIRE_TOOLS


# ── (d) fulfillment_not_connected (missing credential) handled gracefully ─────

def test_fulfillment_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No account connected → schedule_fulfillment_order raises MerchAccountNotConnected.
    monkeypatch.delenv("MERCH_EMPIRE_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="schedule_fulfillment_order",
                      input={"product_id": "merch-premium-hoodie",
                             "design_name": "logo",
                             "quantity": 50}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a print/fulfilment account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "merch-empire",
        "message":   "order 50 hoodies",
        "artist_id": "artist-no-account",
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
    assert actions_evt["fulfillment_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "fulfillment_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_fulfillment_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("MERCH_EMPIRE_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="schedule_fulfillment_order",
                      input={"product_id": "merch-vinyl-lp",
                             "design_name": "album",
                             "quantity": 100}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your fulfilment auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "merch-empire",
        "message":   "press 100 vinyl LPs",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["fulfillment_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "fulfillment_auth_expired"
