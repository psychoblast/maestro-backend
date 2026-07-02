"""
PROOF tests — Miles (tour-commander) Anthropic tool_use loop.

Mirrors tests/test_wire_venue_hawk.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Miles emits search_routing_legs → draft_tour_budget → book_crew_call then a
      final message; all three mock-first tour_commander_service functions are
      invoked with the correct args and the stream surfaces a populated `actions`
      event (actions_taken), with TOUR_COMMANDER_TOOLS passed on every create() call;
  (b) a NON-tour agent (producer-connect) never receives TOUR_COMMANDER_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never TOUR_COMMANDER_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries tour_ops_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / tour-ops calls — the
Anthropic client is faked and the tour_commander_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-tour path."""
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


# ── (a) Miles runs the tool loop and surfaces actions_taken ──────────────────

def test_tour_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected tour-ops account so the crew call succeeds (no network).
    monkeypatch.setenv("TOUR_COMMANDER_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) tour_commander_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, draft_calls, crew_calls = [], [], []
    real_search = m.tour_commander_service.search_routing_legs
    real_draft  = m.tour_commander_service.draft_tour_budget
    real_crew   = m.tour_commander_service.book_crew_call

    async def rec_search(region="", leg_type=""):
        search_calls.append({"region": region, "leg_type": leg_type})
        return await real_search(region=region, leg_type=leg_type)

    async def rec_draft(artist_id, leg_id="", num_shows=0, nightly_guarantee=0):
        draft_calls.append({"artist_id": artist_id, "leg_id": leg_id,
                            "num_shows": num_shows, "nightly_guarantee": nightly_guarantee})
        return await real_draft(artist_id, leg_id=leg_id,
                                num_shows=num_shows, nightly_guarantee=nightly_guarantee)

    async def rec_crew(artist_id, leg_id, call_date, crew_size=0):
        crew_calls.append({"artist_id": artist_id, "leg_id": leg_id,
                           "call_date": call_date, "crew_size": crew_size})
        return await real_crew(artist_id, leg_id, call_date, crew_size)

    monkeypatch.setattr(m.tour_commander_service, "search_routing_legs", rec_search)
    monkeypatch.setattr(m.tour_commander_service, "draft_tour_budget",   rec_draft)
    monkeypatch.setattr(m.tour_commander_service, "book_crew_call",      rec_crew)

    # Scripted Anthropic responses: search → draft → crew call → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_routing_legs",
                      input={"region": "US East", "leg_type": "headline"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_tour_budget",
                      input={"leg_id": "leg-us-east-theatre",
                             "num_shows": 10, "nightly_guarantee": 11000}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="book_crew_call",
                      input={"leg_id": "leg-us-east-theatre",
                             "call_date": "2026-09-01", "crew_size": 8}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I mapped the leg, drafted the budget, and confirmed the crew call.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Miles.
    def _no_stream(**kw):
        raise AssertionError("tour-commander must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "tour-commander",
        "message":   "map a US East headline run and lock the crew",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"region": "US East", "leg_type": "headline"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "leg_id": "leg-us-east-theatre",
        "num_shows": 10, "nightly_guarantee": 11000,
    }], draft_calls
    assert crew_calls == [{
        "artist_id": "artist-9", "leg_id": "leg-us-east-theatre",
        "call_date": "2026-09-01", "crew_size": 8,
    }], crew_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_routing_legs", "draft_tour_budget", "book_crew_call",
    ], tools_used
    assert actions_evt["tour_ops_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "leg(s) found" in by_tool["search_routing_legs"]["result"]
    # known leg, positive shows, positive guarantee, guarantee > per-show cost → viable / run.
    assert "viable=True" in by_tool["draft_tour_budget"]["result"]
    assert "run" in by_tool["draft_tour_budget"]["result"]
    assert by_tool["book_crew_call"]["result"] == "crew call confirmed"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, crew, final.
    assert len(create_calls) == 4
    # TOUR_COMMANDER_TOOLS passed on every tour create call (never other toolsets).
    assert all(kw.get("tools") == m.TOUR_COMMANDER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VENUE_HAWK_TOOLS for kw in create_calls)


# ── (b) Non-tour agent never gets tour tools, takes the unchanged path ────────

def test_non_tour_agent_never_receives_tour_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT tour-commander, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-tour agent must not invoke the tool_use create loop"
    # No actions event for non-tour agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not tour tools ──────

def test_marcus_still_uses_marcus_tools_not_tour(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the tour gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.TOUR_COMMANDER_TOOLS


# ── (d) tour_ops_not_connected (missing credential) handled gracefully ────────

def test_tour_ops_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No tour-ops account connected → book_crew_call raises TourOpsNotConnected.
    monkeypatch.delenv("TOUR_COMMANDER_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="book_crew_call",
                      input={"leg_id": "leg-uk-club",
                             "call_date": "2026-10-10", "crew_size": 6}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a tour-ops account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "tour-commander",
        "message":   "lock the UK crew",
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
    assert actions_evt["tour_ops_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "tour_ops_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_tour_ops_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("TOUR_COMMANDER_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="book_crew_call",
                      input={"leg_id": "leg-eu-support",
                             "call_date": "2026-11-11", "crew_size": 10}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your tour-ops-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "tour-commander",
        "message":   "lock the EU crew",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["tour_ops_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "tour_ops_auth_expired"
