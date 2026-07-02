"""
PROOF tests — Solo (airwave) Anthropic tool_use loop.

Mirrors tests/test_wire_tour_commander.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Solo emits search_airplay_targets → draft_airplay_pitch → submit_airplay_pitch
      then a final message; all three mock-first airwave_service functions are
      invoked with the correct args and the stream surfaces a populated `actions`
      event (actions_taken), with AIRWAVE_TOOLS passed on every create() call;
  (b) a NON-airwave agent (producer-connect) never receives AIRWAVE_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never AIRWAVE_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries plugging_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / plugging calls — the
Anthropic client is faked and the airwave_service boundary is exercised through
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
    """Stand-in for async_client.messages.stream(...) — used by the non-airwave path."""
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


# ── (a) Solo runs the tool loop and surfaces actions_taken ───────────────────

def test_airwave_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected plugging account so the submission succeeds (no network).
    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) airwave_service functions, delegating to the
    # originals so we assert on real, deterministic output.
    search_calls, draft_calls, submit_calls = [], [], []
    real_search = m.airwave_service.search_airplay_targets
    real_draft  = m.airwave_service.draft_airplay_pitch
    real_submit = m.airwave_service.submit_airplay_pitch

    async def rec_search(format="", market=""):
        search_calls.append({"format": format, "market": market})
        return await real_search(format=format, market=market)

    async def rec_draft(artist_id, target_id="", track_title="", release_date=""):
        draft_calls.append({"artist_id": artist_id, "target_id": target_id,
                            "track_title": track_title, "release_date": release_date})
        return await real_draft(artist_id, target_id=target_id,
                                track_title=track_title, release_date=release_date)

    async def rec_submit(artist_id, target_id, track_title, release_date=""):
        submit_calls.append({"artist_id": artist_id, "target_id": target_id,
                             "track_title": track_title, "release_date": release_date})
        return await real_submit(artist_id, target_id, track_title, release_date)

    monkeypatch.setattr(m.airwave_service, "search_airplay_targets", rec_search)
    monkeypatch.setattr(m.airwave_service, "draft_airplay_pitch",    rec_draft)
    monkeypatch.setattr(m.airwave_service, "submit_airplay_pitch",   rec_submit)

    # Scripted Anthropic responses: search → draft → submit → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_airplay_targets",
                      input={"format": "indie", "market": "Global"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_airplay_pitch",
                      input={"target_id": "tgt-indie-pop-list",
                             "track_title": "Neon Skyline",
                             "release_date": "2026-09-01"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="submit_airplay_pitch",
                      input={"target_id": "tgt-indie-pop-list",
                             "track_title": "Neon Skyline",
                             "release_date": "2026-09-01"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the target, drafted the pitch, and submitted it.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Solo.
    def _no_stream(**kw):
        raise AssertionError("airwave must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "airwave",
        "message":   "pitch my single to indie playlists",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"format": "indie", "market": "Global"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "target_id": "tgt-indie-pop-list",
        "track_title": "Neon Skyline", "release_date": "2026-09-01",
    }], draft_calls
    assert submit_calls == [{
        "artist_id": "artist-9", "target_id": "tgt-indie-pop-list",
        "track_title": "Neon Skyline", "release_date": "2026-09-01",
    }], submit_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_airplay_targets", "draft_airplay_pitch", "submit_airplay_pitch",
    ], tools_used
    assert actions_evt["plugging_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "target(s) found" in by_tool["search_airplay_targets"]["result"]
    # known target, present track + release date → viable / send.
    assert "viable=True" in by_tool["draft_airplay_pitch"]["result"]
    assert "send" in by_tool["draft_airplay_pitch"]["result"]
    assert by_tool["submit_airplay_pitch"]["result"] == "airplay pitch submitted"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, submit, final.
    assert len(create_calls) == 4
    # AIRWAVE_TOOLS passed on every airwave create call (never other toolsets).
    assert all(kw.get("tools") == m.AIRWAVE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.TOUR_COMMANDER_TOOLS for kw in create_calls)


# ── (b) Non-airwave agent never gets airwave tools, unchanged path ────────────

def test_non_airwave_agent_never_receives_airwave_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT airwave, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-airwave agent must not invoke the tool_use create loop"
    # No actions event for non-airwave agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not airwave tools ───

def test_marcus_still_uses_marcus_tools_not_airwave(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the airwave gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.AIRWAVE_TOOLS


# ── (d) plugging_not_connected (missing credential) handled gracefully ────────

def test_plugging_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No plugging account connected → submit_airplay_pitch raises AirwaveAccountNotConnected.
    monkeypatch.delenv("AIRWAVE_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="submit_airplay_pitch",
                      input={"target_id": "tgt-kexp-drive",
                             "track_title": "Midnight Radio",
                             "release_date": "2026-10-10"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a plugging account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "airwave",
        "message":   "submit my pitch to KEXP",
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
    assert actions_evt["plugging_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "plugging_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_plugging_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("AIRWAVE_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="submit_airplay_pitch",
                      input={"target_id": "tgt-fresh-finds",
                             "track_title": "Golden Hour",
                             "release_date": "2026-11-11"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your plugging-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "airwave",
        "message":   "submit my pitch to Fresh Finds",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["plugging_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "plugging_auth_expired"
