"""
PROOF tests — Scout (ar-scout) Anthropic tool_use loop.

Mirrors tests/test_wire_venue_hawk.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Scout emits search_prospects → evaluate_demo → log_scouting_note then a
      final message; all three mock-first ar_scout_service functions are invoked
      with the correct args and the stream surfaces a populated `actions` event
      (actions_taken), with AR_SCOUT_TOOLS passed on every create() call;
  (b) a NON-scout agent (producer-connect) never receives AR_SCOUT_TOOLS — it takes
      the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never AR_SCOUT_TOOLS;
  (d) the CRM-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries ar_scout_crm_not_connected=True);
  (e) expired CRM auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / CRM calls — the
Anthropic client is faked and the ar_scout_service boundary is exercised through
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


# ── (a) Scout runs the tool loop and surfaces actions_taken ──────────────────

def test_ar_scout_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected A&R CRM so the note logs (no network).
    monkeypatch.setenv("AR_SCOUT_CRM_CONNECTED", "true")

    # Record calls into the REAL (pure) ar_scout_service functions, delegating to
    # the originals so we assert on real, deterministic output.
    search_calls, eval_calls, note_calls = [], [], []
    real_search = m.ar_scout_service.search_prospects
    real_eval   = m.ar_scout_service.evaluate_demo
    real_note   = m.ar_scout_service.log_scouting_note

    async def rec_search(genre="", region="", stage=""):
        search_calls.append({"genre": genre, "region": region, "stage": stage})
        return await real_search(genre=genre, region=region, stage=stage)

    async def rec_eval(artist_id, track_title="", genre=""):
        eval_calls.append({"artist_id": artist_id, "track_title": track_title, "genre": genre})
        return await real_eval(artist_id, track_title=track_title, genre=genre)

    async def rec_note(artist_id, prospect_id, note="", rating=0):
        note_calls.append({"artist_id": artist_id, "prospect_id": prospect_id,
                           "note": note, "rating": rating})
        return await real_note(artist_id, prospect_id, note, rating)

    monkeypatch.setattr(m.ar_scout_service, "search_prospects",  rec_search)
    monkeypatch.setattr(m.ar_scout_service, "evaluate_demo",     rec_eval)
    monkeypatch.setattr(m.ar_scout_service, "log_scouting_note", rec_note)

    # Scripted Anthropic responses: search → evaluate → log → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_prospects",
                      input={"genre": "indie", "stage": "buzzing"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="evaluate_demo",
                      input={"track_title": "Midnight Line", "genre": "indie"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="log_scouting_note",
                      input={"prospect_id": "pro-neon-hollow",
                             "note": "strong hook, worth tracking", "rating": 8}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the prospect, scored the demo, and logged a note.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Scout.
    def _no_stream(**kw):
        raise AssertionError("ar-scout must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ar-scout",
        "message":   "find me a buzzing indie prospect and score their demo",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"genre": "indie", "region": "", "stage": "buzzing"}], search_calls
    assert eval_calls == [{
        "artist_id": "artist-9", "track_title": "Midnight Line", "genre": "indie",
    }], eval_calls
    assert note_calls == [{
        "artist_id": "artist-9", "prospect_id": "pro-neon-hollow",
        "note": "strong hook, worth tracking", "rating": 8,
    }], note_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_prospects", "evaluate_demo", "log_scouting_note",
    ], tools_used
    assert actions_evt["ar_scout_crm_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "prospect(s) found" in by_tool["search_prospects"]["result"]
    # a track title + genre present → a numeric composite and a real recommendation.
    assert "composite=" in by_tool["evaluate_demo"]["result"]
    assert any(rec in by_tool["evaluate_demo"]["result"]
               for rec in ("sign_track", "develop", "pass")), by_tool["evaluate_demo"]["result"]
    assert by_tool["log_scouting_note"]["result"] == "scouting note logged"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, evaluate, log, final.
    assert len(create_calls) == 4
    # AR_SCOUT_TOOLS passed on every scout create call (never other toolsets).
    assert all(kw.get("tools") == m.AR_SCOUT_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VENUE_HAWK_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.DATA_ORACLE_TOOLS for kw in create_calls)


# ── (b) Non-scout agent never gets scout tools, takes the unchanged path ──────

def test_non_scout_agent_never_receives_ar_scout_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT ar-scout, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-scout agent must not invoke the tool_use create loop"
    # No actions event for non-scout agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not scout tools ─────

def test_marcus_still_uses_marcus_tools_not_ar_scout(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the scout gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.AR_SCOUT_TOOLS


# ── (d) ar_scout_crm_not_connected (missing credential) handled gracefully ────

def test_ar_scout_crm_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No CRM connected → log raises ArScoutCRMNotConnected.
    monkeypatch.delenv("AR_SCOUT_CRM_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="log_scouting_note",
                      input={"prospect_id": "pro-velvet-signal",
                             "note": "keep an eye on this one", "rating": 7}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect an A&R CRM first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ar-scout",
        "message":   "log a note on Velvet Signal",
        "artist_id": "artist-no-crm",
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
    assert actions_evt["ar_scout_crm_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "ar_scout_crm_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_ar_scout_crm_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("AR_SCOUT_CRM_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="log_scouting_note",
                      input={"prospect_id": "pro-paper-anthem",
                             "note": "radio-ready", "rating": 6}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your A&R CRM auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "ar-scout",
        "message":   "log a note on Paper Anthem",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["ar_scout_crm_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "ar_scout_crm_auth_expired"
