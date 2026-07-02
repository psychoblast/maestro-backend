"""
PROOF tests — Nia (brand-connect) Anthropic tool_use loop.

Mirrors tests/test_wire_airwave.py / tests/test_marcus_tool_use.py. Proves that,
in /api/chat_stream:

  (a) Nia emits search_brand_partners → draft_partnership_proposal →
      submit_partnership_proposal then a final message; all three mock-first
      brand_connect_service functions are invoked with the correct args and the
      stream surfaces a populated `actions` event (actions_taken), with
      BRAND_CONNECT_TOOLS passed on every create() call;
  (b) a NON-brand-connect agent (producer-connect) never receives BRAND_CONNECT_TOOLS — it
      takes the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never BRAND_CONNECT_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries partnerships_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / partnership calls —
the Anthropic client is faked and the brand_connect_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-brand-connect path."""
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


# ── (a) Nia runs the tool loop and surfaces actions_taken ────────────────────

def test_brand_connect_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected brand-partnerships account so the submission succeeds (no network).
    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) brand_connect_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, draft_calls, submit_calls = [], [], []
    real_search = m.brand_connect_service.search_brand_partners
    real_draft  = m.brand_connect_service.draft_partnership_proposal
    real_submit = m.brand_connect_service.submit_partnership_proposal

    async def rec_search(category="", budget_tier=""):
        search_calls.append({"category": category, "budget_tier": budget_tier})
        return await real_search(category=category, budget_tier=budget_tier)

    async def rec_draft(artist_id, brand_id="", campaign_type="", fee=0):
        draft_calls.append({"artist_id": artist_id, "brand_id": brand_id,
                            "campaign_type": campaign_type, "fee": fee})
        return await real_draft(artist_id, brand_id=brand_id,
                                campaign_type=campaign_type, fee=fee)

    async def rec_submit(artist_id, brand_id, campaign_type, fee=0):
        submit_calls.append({"artist_id": artist_id, "brand_id": brand_id,
                             "campaign_type": campaign_type, "fee": fee})
        return await real_submit(artist_id, brand_id, campaign_type, fee)

    monkeypatch.setattr(m.brand_connect_service, "search_brand_partners",       rec_search)
    monkeypatch.setattr(m.brand_connect_service, "draft_partnership_proposal",  rec_draft)
    monkeypatch.setattr(m.brand_connect_service, "submit_partnership_proposal", rec_submit)

    # Scripted Anthropic responses: search → draft → submit → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_brand_partners",
                      input={"category": "apparel", "budget_tier": "growth"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_partnership_proposal",
                      input={"brand_id": "brand-v612-apparel",
                             "campaign_type": "endorsement",
                             "fee": 20000}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="submit_partnership_proposal",
                      input={"brand_id": "brand-v612-apparel",
                             "campaign_type": "endorsement",
                             "fee": 20000}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the brand, drafted the proposal, and submitted it.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Nia.
    def _no_stream(**kw):
        raise AssertionError("brand-connect must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "brand-connect",
        "message":   "pitch my endorsement to an apparel brand",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"category": "apparel", "budget_tier": "growth"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "brand_id": "brand-v612-apparel",
        "campaign_type": "endorsement", "fee": 20000,
    }], draft_calls
    assert submit_calls == [{
        "artist_id": "artist-9", "brand_id": "brand-v612-apparel",
        "campaign_type": "endorsement", "fee": 20000,
    }], submit_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_brand_partners", "draft_partnership_proposal", "submit_partnership_proposal",
    ], tools_used
    assert actions_evt["partnerships_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "brand(s) found" in by_tool["search_brand_partners"]["result"]
    # known brand, present campaign type + fee → viable / send.
    assert "viable=True" in by_tool["draft_partnership_proposal"]["result"]
    assert "send" in by_tool["draft_partnership_proposal"]["result"]
    assert by_tool["submit_partnership_proposal"]["result"] == "partnership proposal submitted"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, submit, final.
    assert len(create_calls) == 4
    # BRAND_CONNECT_TOOLS passed on every brand-connect create call (never other toolsets).
    assert all(kw.get("tools") == m.BRAND_CONNECT_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.AIRWAVE_TOOLS for kw in create_calls)


# ── (b) Non-brand-connect agent never gets brand tools, unchanged path ────────

def test_non_brand_connect_agent_never_receives_brand_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT brand-connect, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-brand-connect agent must not invoke the tool_use create loop"
    # No actions event for non-brand-connect agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not brand tools ─────

def test_marcus_still_uses_marcus_tools_not_brand_connect(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the brand-connect gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.BRAND_CONNECT_TOOLS


# ── (d) partnerships_not_connected (missing credential) handled gracefully ────

def test_partnerships_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No account connected → submit_partnership_proposal raises BrandConnectAccountNotConnected.
    monkeypatch.delenv("BRAND_CONNECT_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="submit_partnership_proposal",
                      input={"brand_id": "brand-solace-audio",
                             "campaign_type": "sponsorship",
                             "fee": 40000}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a brand-partnerships account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "brand-connect",
        "message":   "submit my proposal to Solace Audio",
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
    assert actions_evt["partnerships_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "partnerships_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_partnerships_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("BRAND_CONNECT_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="submit_partnership_proposal",
                      input={"brand_id": "brand-pulse-gaming",
                             "campaign_type": "sponsorship",
                             "fee": 55000}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your brand-partnerships auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "brand-connect",
        "message":   "submit my proposal to Pulse Gaming",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["partnerships_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "partnerships_auth_expired"
