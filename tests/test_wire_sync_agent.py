"""
PROOF tests — Sync (sync-agent) Anthropic tool_use loop.

Mirrors tests/test_wire_vault_keeper.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Sync emits search_sync_briefs → assess_track_sync_fit → submit_sync_pitch
      then a final message; all three mock-first sync_agent_service functions are
      invoked with the correct args and the stream surfaces a populated `actions`
      event (actions_taken), with SYNC_AGENT_TOOLS passed on every create() call;
  (b) a NON-sync agent (producer-connect) never receives SYNC_AGENT_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never SYNC_AGENT_TOOLS;
  (d) the catalogue-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries sync_catalogue_not_connected=True);
  (e) expired catalogue auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / marketplace calls —
the Anthropic client is faked and the sync_agent_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-sync path."""
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


# ── (a) Sync runs the tool loop and surfaces actions_taken ───────────────────

def test_sync_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected sync catalogue so the pitch succeeds (no network).
    monkeypatch.setenv("SYNC_AGENT_CATALOGUE_CONNECTED", "true")

    # Record calls into the REAL (pure) sync_agent_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, assess_calls, pitch_calls = [], [], []
    real_search = m.sync_agent_service.search_sync_briefs
    real_assess = m.sync_agent_service.assess_track_sync_fit
    real_pitch  = m.sync_agent_service.submit_sync_pitch

    async def rec_search(medium="", genre=""):
        search_calls.append({"medium": medium, "genre": genre})
        return await real_search(medium=medium, genre=genre)

    async def rec_assess(artist_id, brief_id="", track_title="", genre="",
                         tempo_bpm=0, has_instrumental=False):
        assess_calls.append({"artist_id": artist_id, "brief_id": brief_id,
                             "track_title": track_title, "genre": genre,
                             "tempo_bpm": tempo_bpm, "has_instrumental": has_instrumental})
        return await real_assess(artist_id, brief_id=brief_id, track_title=track_title,
                                 genre=genre, tempo_bpm=tempo_bpm,
                                 has_instrumental=has_instrumental)

    async def rec_pitch(artist_id, brief_id, track_title, note=""):
        pitch_calls.append({"artist_id": artist_id, "brief_id": brief_id,
                            "track_title": track_title, "note": note})
        return await real_pitch(artist_id, brief_id, track_title, note)

    monkeypatch.setattr(m.sync_agent_service, "search_sync_briefs",    rec_search)
    monkeypatch.setattr(m.sync_agent_service, "assess_track_sync_fit", rec_assess)
    monkeypatch.setattr(m.sync_agent_service, "submit_sync_pitch",     rec_pitch)

    # Scripted Anthropic responses: search → assess → pitch → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_sync_briefs",
                      input={"medium": "ad", "genre": "pop"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="assess_track_sync_fit",
                      input={"brief_id": "brief-ad-national-pop",
                             "track_title": "Sunrise", "genre": "pop",
                             "tempo_bpm": 120, "has_instrumental": True}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="submit_sync_pitch",
                      input={"brief_id": "brief-ad-national-pop",
                             "track_title": "Sunrise", "note": "great fit"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found a brief, assessed your track, and submitted the pitch.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Sync.
    def _no_stream(**kw):
        raise AssertionError("sync-agent must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "sync-agent",
        "message":   "find an ad brief for my pop track and pitch it",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"medium": "ad", "genre": "pop"}], search_calls
    assert assess_calls == [{
        "artist_id": "artist-9", "brief_id": "brief-ad-national-pop",
        "track_title": "Sunrise", "genre": "pop",
        "tempo_bpm": 120, "has_instrumental": True,
    }], assess_calls
    assert pitch_calls == [{
        "artist_id": "artist-9", "brief_id": "brief-ad-national-pop",
        "track_title": "Sunrise", "note": "great fit",
    }], pitch_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_sync_briefs", "assess_track_sync_fit", "submit_sync_pitch",
    ], tools_used
    assert actions_evt["sync_catalogue_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "brief(s) found" in by_tool["search_sync_briefs"]["result"]
    # genre + tempo-in-window + instrumental present → fit / proceed.
    assert "fit=True" in by_tool["assess_track_sync_fit"]["result"]
    assert "proceed" in by_tool["assess_track_sync_fit"]["result"]
    assert by_tool["submit_sync_pitch"]["result"] == "pitch submitted"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, assess, pitch, final.
    assert len(create_calls) == 4
    # SYNC_AGENT_TOOLS passed on every sync create call (never other toolsets).
    assert all(kw.get("tools") == m.SYNC_AGENT_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VAULT_KEEPER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.FAN_BUILDER_TOOLS for kw in create_calls)


# ── (b) Non-sync agent never gets sync tools, takes the unchanged path ────────

def test_non_sync_agent_never_receives_sync_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT sync-agent, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-sync agent must not invoke the tool_use create loop"
    # No actions event for non-sync agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not sync tools ──────

def test_marcus_still_uses_marcus_tools_not_sync(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the sync gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.SYNC_AGENT_TOOLS


# ── (d) sync_catalogue_not_connected (missing credential) handled gracefully ──

def test_sync_catalogue_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No sync catalogue connected → submit raises SyncCatalogueNotConnected.
    monkeypatch.delenv("SYNC_AGENT_CATALOGUE_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="submit_sync_pitch",
                      input={"brief_id": "brief-tv-drama-indie",
                             "track_title": "Quiet Hours"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a sync catalogue first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "sync-agent",
        "message":   "pitch my track to the TV drama brief",
        "artist_id": "artist-no-catalogue",
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
    assert actions_evt["sync_catalogue_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "sync_catalogue_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_sync_catalogue_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("SYNC_AGENT_CATALOGUE_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="submit_sync_pitch",
                      input={"brief_id": "brief-film-trailer-epic",
                             "track_title": "Rise"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your sync-catalogue auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "sync-agent",
        "message":   "pitch my track to the film trailer brief",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["sync_catalogue_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "sync_catalogue_auth_expired"
