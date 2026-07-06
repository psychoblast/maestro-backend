"""
PROOF tests — Ray B (venue-hawk) Anthropic tool_use loop (U2 OUTREACH rework).

Mirrors tests/test_wire_brand_connect.py / test_wire_airwave.py. Proves that, in
/api/chat_stream:

  (a) Ray B emits search_venues → submit_booking_hold → lookup_booking_doctrine →
      send_booking_inquiry then a final message; all four mock-first
      venue_hawk_service functions are invoked with the correct args and the stream
      surfaces a populated `actions` event, with VENUE_HAWK_TOOLS passed on every
      create() call. search_venues NEVER fabricates a venue (it filters the
      artist-supplied list); submit_booking_hold records state and does not send;
      send_booking_inquiry is the gated mock send with the model-written body;
  (b) a NON-venue agent (music-edu) never receives VENUE_HAWK_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never VENUE_HAWK_TOOLS;
  (d) the account-not-connected (missing-credential) path on send_booking_inquiry
      is handled gracefully (no crash; actions carries venue_booking_not_connected);
  (e) expired account auth also degrades to the not-connected path;
  (f) this (newest) unit OWNS the exact venue-hawk tool roster; and
  (g) the service tool layer contains NO LLM send seam (AST-enforced).

Everything is in-process and deterministic. NO network / LLM / booking calls — the
Anthropic client is faked and the venue_hawk_service boundary is exercised through
recording wrappers over the REAL (pure, mock-first) functions.
"""
import ast
import importlib
import json
import pathlib
from unittest.mock import MagicMock, patch

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


# Artist-supplied venue list — the ONLY source of venue names Ray B ever sees.
_ARTIST_VENUES = [
    {"name": "The Corner Room", "market": "New York", "capacity_tier": "theatre", "genre": "indie"},
    {"name": "Riverside Bar",   "market": "Austin",   "capacity_tier": "club",    "genre": "indie"},
]


# ── (a) Ray B runs the full tool loop and surfaces actions_taken ─────────────

def test_venue_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected booking account so the inquiry send succeeds (no network).
    monkeypatch.setenv("VENUE_HAWK_ACCOUNT_CONNECTED", "true")

    search_calls, hold_calls, doctrine_calls, send_calls = [], [], [], []
    real_search   = m.venue_hawk_service.search_venues
    real_hold     = m.venue_hawk_service.submit_booking_hold
    real_doctrine = m.venue_hawk_service.lookup_booking_doctrine
    real_send     = m.venue_hawk_service.send_booking_inquiry

    async def rec_search(market="", capacity_tier="", genre="", venue_list=None):
        search_calls.append({"market": market, "capacity_tier": capacity_tier,
                             "genre": genre, "venue_list": venue_list})
        return await real_search(market=market, capacity_tier=capacity_tier,
                                 genre=genre, venue_list=venue_list)

    async def rec_hold(artist_id, venue="", venue_id="", show_dates=None, act="",
                       deal_structure="", hold_type="first"):
        hold_calls.append({"artist_id": artist_id, "venue": venue, "venue_id": venue_id,
                           "show_dates": show_dates, "act": act,
                           "deal_structure": deal_structure, "hold_type": hold_type})
        return await real_hold(artist_id, venue=venue, venue_id=venue_id,
                               show_dates=show_dates, act=act,
                               deal_structure=deal_structure, hold_type=hold_type)

    async def rec_doctrine(topic=""):
        doctrine_calls.append({"topic": topic})
        return await real_doctrine(topic)

    async def rec_send(artist_id, venue_id="", venue="", subject="", body=""):
        send_calls.append({"artist_id": artist_id, "venue_id": venue_id,
                           "venue": venue, "subject": subject, "body": body})
        return await real_send(artist_id, venue_id=venue_id, venue=venue,
                               subject=subject, body=body)

    monkeypatch.setattr(m.venue_hawk_service, "search_venues",          rec_search)
    monkeypatch.setattr(m.venue_hawk_service, "submit_booking_hold",    rec_hold)
    monkeypatch.setattr(m.venue_hawk_service, "lookup_booking_doctrine", rec_doctrine)
    monkeypatch.setattr(m.venue_hawk_service, "send_booking_inquiry",   rec_send)

    # Scripted responses: search → hold → doctrine → send → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_venues",
                      input={"market": "New York", "capacity_tier": "theatre",
                             "venue_list": _ARTIST_VENUES}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="submit_booking_hold",
                      input={"venue": "The Corner Room", "show_dates": ["2026-09-01"],
                             "act": "The Act", "deal_structure": "door split",
                             "hold_type": "first"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="lookup_booking_doctrine",
                      input={"topic": "hold_system"}, id="t3")], "tool_use"),
        _Resp([_Block("tool_use", name="send_booking_inquiry",
                      input={"venue": "The Corner Room", "subject": "Avails?",
                             "body": "Hi — checking Sept avails for The Act."}, id="t4")], "tool_use"),
        _Resp([_Block("text", text="Done — filtered the room, recorded the hold, and sent the inquiry.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    def _no_stream(**kw):
        raise AssertionError("venue-hawk must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "venue-hawk",
        "message":   "find me a NY theatre from my list and start an inquiry",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # search_venues filtered the ARTIST-supplied list (never fabricated).
    assert len(search_calls) == 1
    assert search_calls[0]["market"] == "New York"
    assert search_calls[0]["venue_list"] == _ARTIST_VENUES
    # submit_booking_hold recorded state (not a send).
    assert hold_calls == [{
        "artist_id": "artist-9", "venue": "The Corner Room", "venue_id": "",
        "show_dates": ["2026-09-01"], "act": "The Act",
        "deal_structure": "door split", "hold_type": "first",
    }], hold_calls
    assert doctrine_calls == [{"topic": "hold_system"}], doctrine_calls
    # send_booking_inquiry carried the MODEL-written body verbatim.
    assert send_calls == [{
        "artist_id": "artist-9", "venue_id": "", "venue": "The Corner Room",
        "subject": "Avails?", "body": "Hi — checking Sept avails for The Act.",
    }], send_calls

    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_venues", "submit_booking_hold", "lookup_booking_doctrine",
        "send_booking_inquiry",
    ], tools_used
    assert actions_evt["venue_booking_not_connected"] is False

    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "artist-supplied venue(s) matched" in by_tool["search_venues"]["result"]
    assert "hold request recorded" in by_tool["submit_booking_hold"]["result"]
    assert "honesty rule(s)" in by_tool["lookup_booking_doctrine"]["result"]
    assert by_tool["send_booking_inquiry"]["result"] == "booking inquiry sent"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Five create() round-trips: search, hold, doctrine, send, final.
    assert len(create_calls) == 5
    assert all(kw.get("tools") == m.VENUE_HAWK_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LIVE_WIRE_TOOLS for kw in create_calls)


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
        "agent_id":  "music-edu",   # NOT venue-hawk, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    assert create_calls == [], "non-venue agent must not invoke the tool_use create loop"
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
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.VENUE_HAWK_TOOLS


# ── (d) venue_booking_not_connected (missing credential) handled gracefully ───

def test_venue_booking_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No booking account connected → send_booking_inquiry raises VenueBookingNotConnected.
    monkeypatch.delenv("VENUE_HAWK_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="send_booking_inquiry",
                      input={"venue": "The Corner Room", "subject": "Avails?",
                             "body": "Hi — checking dates."}, id="t1")], "tool_use"),
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
        "message":   "send the inquiry to the Corner Room",
        "artist_id": "artist-no-account",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

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
        _Resp([_Block("tool_use", name="send_booking_inquiry",
                      input={"venue": "Riverside Bar", "subject": "Avails?",
                             "body": "Hi — checking dates."}, id="t1")], "tool_use"),
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
        "message":   "send the inquiry to Riverside",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["venue_booking_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "venue_booking_auth_expired"


# ── (f) newest unit OWNS the exact venue-hawk tool roster ────────────────────

def test_venue_hawk_tool_roster_is_exact(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)
    names = [t["name"] for t in m.VENUE_HAWK_TOOLS]
    assert names == ["search_venues", "submit_booking_hold",
                     "lookup_booking_doctrine", "send_booking_inquiry"], names
    # the fabricated-directory draft_show_offer was removed this build.
    assert "draft_show_offer" not in names


# ── (g) the service tool layer carries NO LLM send seam (AST-enforced) ───────

def test_service_layer_has_no_llm_send_seam():
    import venue_hawk_service as vhs
    source = pathlib.Path(vhs.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    # No import of an LLM SDK.
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert "anthropic" not in a.name.lower(), a.name
        if isinstance(node, ast.ImportFrom):
            assert "anthropic" not in (node.module or "").lower(), node.module
    # No `*.messages.create(...)` model send call anywhere.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "create" and isinstance(node.func.value, ast.Attribute):
                assert node.func.value.attr != "messages", "no messages.create in the tool layer"
