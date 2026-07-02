"""
PROOF tests — Ray B (venue-hawk) Anthropic tool_use loop.

Mirrors tests/test_wire_vault_keeper.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Ray B emits search_venues → draft_show_offer → submit_booking_hold then a
      final message; all three mock-first venue_hawk_service functions are invoked
      with the correct args and the stream surfaces a populated `actions` event
      (actions_taken), with VENUE_HAWK_TOOLS passed on every create() call;
  (b) a NON-venue agent (producer-connect) never receives VENUE_HAWK_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never VENUE_HAWK_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries venue_booking_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / booking calls — the
Anthropic client is faked and the venue_hawk_service boundary is exercised through
recording wrappers over the REAL (pure, mock-first) functions.
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
    """Stand-in for async_client.messages.stream(...) — used by the non-venue path."""
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


# ── (a) Ray B runs the tool loop and surfaces actions_taken ──────────────────

def test_venue_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected booking account so the hold succeeds (no network).
    monkeypatch.setenv("VENUE_HAWK_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) venue_hawk_service functions, delegating to
    # the originals so we assert on real, deterministic output.
    search_calls, draft_calls, hold_calls = [], [], []
    real_search = m.venue_hawk_service.search_venues
    real_draft  = m.venue_hawk_service.draft_show_offer
    real_hold   = m.venue_hawk_service.submit_booking_hold

    async def rec_search(market="", capacity_tier=""):
        search_calls.append({"market": market, "capacity_tier": capacity_tier})
        return await real_search(market=market, capacity_tier=capacity_tier)

    async def rec_draft(artist_id, venue_id="", show_date="", guarantee=0):
        draft_calls.append({"artist_id": artist_id, "venue_id": venue_id,
                            "show_date": show_date, "guarantee": guarantee})
        return await real_draft(artist_id, venue_id=venue_id,
                                show_date=show_date, guarantee=guarantee)

    async def rec_hold(artist_id, venue_id, show_date, guarantee=0):
        hold_calls.append({"artist_id": artist_id, "venue_id": venue_id,
                           "show_date": show_date, "guarantee": guarantee})
        return await real_hold(artist_id, venue_id, show_date, guarantee)

    monkeypatch.setattr(m.venue_hawk_service, "search_venues",       rec_search)
    monkeypatch.setattr(m.venue_hawk_service, "draft_show_offer",    rec_draft)
    monkeypatch.setattr(m.venue_hawk_service, "submit_booking_hold", rec_hold)

    # Scripted Anthropic responses: search → draft → hold → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_venues",
                      input={"market": "New York", "capacity_tier": "theatre"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_show_offer",
                      input={"venue_id": "ven-mercury-hall",
                             "show_date": "2026-09-01", "guarantee": 5000}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="submit_booking_hold",
                      input={"venue_id": "ven-mercury-hall",
                             "show_date": "2026-09-01", "guarantee": 5000}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the room, drafted the offer, and placed the hold.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Ray B.
    def _no_stream(**kw):
        raise AssertionError("venue-hawk must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "venue-hawk",
        "message":   "find me a NY theatre and hold a date",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"market": "New York", "capacity_tier": "theatre"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "venue_id": "ven-mercury-hall",
        "show_date": "2026-09-01", "guarantee": 5000,
    }], draft_calls
    assert hold_calls == [{
        "artist_id": "artist-9", "venue_id": "ven-mercury-hall",
        "show_date": "2026-09-01", "guarantee": 5000,
    }], hold_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_venues", "draft_show_offer", "submit_booking_hold",
    ], tools_used
    assert actions_evt["venue_booking_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "venue(s) found" in by_tool["search_venues"]["result"]
    # date present, venue known, positive guarantee → viable / send.
    assert "viable=True" in by_tool["draft_show_offer"]["result"]
    assert "send" in by_tool["draft_show_offer"]["result"]
    assert by_tool["submit_booking_hold"]["result"] == "booking hold placed"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, hold, final.
    assert len(create_calls) == 4
    # VENUE_HAWK_TOOLS passed on every venue create call (never other toolsets).
    assert all(kw.get("tools") == m.VENUE_HAWK_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VAULT_KEEPER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.DESIGN_STUDIO_TOOLS for kw in create_calls)


# ── (b) Non-venue agent never gets venue tools, takes the unchanged path ──────

def test_non_venue_agent_never_receives_venue_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT venue-hawk, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-venue agent must not invoke the tool_use create loop"
    # No actions event for non-venue agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not venue tools ─────

def test_marcus_still_uses_marcus_tools_not_venue(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the venue gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.VENUE_HAWK_TOOLS


# ── (d) venue_booking_not_connected (missing credential) handled gracefully ───

def test_venue_booking_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No booking account connected → submit raises VenueBookingNotConnected.
    monkeypatch.delenv("VENUE_HAWK_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="submit_booking_hold",
                      input={"venue_id": "ven-echo-club",
                             "show_date": "2026-10-10", "guarantee": 2000}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a booking account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "venue-hawk",
        "message":   "hold the Echo Club",
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
    assert actions_evt["venue_booking_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "venue_booking_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_venue_booking_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("VENUE_HAWK_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="submit_booking_hold",
                      input={"venue_id": "ven-fillmore-west",
                             "show_date": "2026-11-11", "guarantee": 4000}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your booking-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "venue-hawk",
        "message":   "hold the Fillmore",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["venue_booking_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "venue_booking_auth_expired"
