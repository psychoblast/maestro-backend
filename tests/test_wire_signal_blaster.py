"""
PROOF tests — Zara (signal-blaster) Anthropic tool_use loop.

Mirrors tests/test_wire_ledger_lock.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Zara emits search_media_outlets → draft_press_release → send_press_pitch
      then a final message; all three mock-first signal_blaster_service functions
      are invoked with the correct args and the stream surfaces a populated
      `actions` event (actions_taken), with SIGNAL_BLASTER_TOOLS passed on every
      create() call;
  (b) a NON-signal agent (producer-connect) never receives SIGNAL_BLASTER_TOOLS — it takes
      the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never SIGNAL_BLASTER_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries press_account_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / press-wire calls —
the Anthropic client is faked and the signal_blaster_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-signal path."""
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


# ── (a) Zara runs the tool loop and surfaces actions_taken ───────────────────

def test_signal_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected press account so the pitch send succeeds (no network).
    monkeypatch.setenv("SIGNAL_BLASTER_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) signal_blaster_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, draft_calls, send_calls = [], [], []
    real_search = m.signal_blaster_service.search_media_outlets
    real_draft  = m.signal_blaster_service.draft_press_release
    real_send   = m.signal_blaster_service.send_press_pitch

    async def rec_search(beat="", tier=""):
        search_calls.append({"beat": beat, "tier": tier})
        return await real_search(beat=beat, tier=tier)

    async def rec_draft(artist_id, headline="", angle="", quote=""):
        draft_calls.append({"artist_id": artist_id, "headline": headline,
                            "angle": angle, "quote": quote})
        return await real_draft(artist_id, headline=headline, angle=angle, quote=quote)

    async def rec_send(artist_id, outlet_id, subject, body=""):
        send_calls.append({"artist_id": artist_id, "outlet_id": outlet_id,
                           "subject": subject, "body": body})
        return await real_send(artist_id, outlet_id, subject, body)

    monkeypatch.setattr(m.signal_blaster_service, "search_media_outlets", rec_search)
    monkeypatch.setattr(m.signal_blaster_service, "draft_press_release",  rec_draft)
    monkeypatch.setattr(m.signal_blaster_service, "send_press_pitch",     rec_send)

    # Scripted Anthropic responses: search → draft → send → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_media_outlets",
                      input={"beat": "indie", "tier": "A"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_press_release",
                      input={"headline": "New Single Out Now",
                             "angle": "Debut single from rising indie artist",
                             "quote": "This song is everything to me"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="send_press_pitch",
                      input={"outlet_id": "out-pitchfork", "subject": "Pitch: New Single",
                             "body": "Please consider covering this release."}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the outlet, drafted the release, and sent your pitch.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Zara.
    def _no_stream(**kw):
        raise AssertionError("signal-blaster must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "signal-blaster",
        "message":   "find indie press, draft a release, and pitch my single",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"beat": "indie", "tier": "A"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "headline": "New Single Out Now",
        "angle": "Debut single from rising indie artist",
        "quote": "This song is everything to me",
    }], draft_calls
    assert send_calls == [{
        "artist_id": "artist-9", "outlet_id": "out-pitchfork",
        "subject": "Pitch: New Single",
        "body": "Please consider covering this release.",
    }], send_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_media_outlets", "draft_press_release", "send_press_pitch",
    ], tools_used
    assert actions_evt["press_account_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "outlet(s) found" in by_tool["search_media_outlets"]["result"]
    # headline + angle present → drafted / publish.
    assert "drafted=True" in by_tool["draft_press_release"]["result"]
    assert "publish" in by_tool["draft_press_release"]["result"]
    assert by_tool["send_press_pitch"]["result"] == "press pitch sent"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, send, final.
    assert len(create_calls) == 4
    # SIGNAL_BLASTER_TOOLS passed on every signal create call (never other toolsets).
    assert all(kw.get("tools") == m.SIGNAL_BLASTER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.FUND_PHANTOM_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.RIGHTS_PULSE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.BORDER_ROYALTY_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MECH_LEDGER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VAULT_KEEPER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEDGER_LOCK_TOOLS for kw in create_calls)


# ── (b) Non-signal agent never gets signal tools, takes the unchanged path ────

def test_non_signal_agent_never_receives_signal_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT signal-blaster, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-signal agent must not invoke the tool_use create loop"
    # No actions event for non-signal agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not signal tools ────

def test_marcus_still_uses_marcus_tools_not_signal(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the signal gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.SIGNAL_BLASTER_TOOLS


# ── (d) press_account_not_connected (missing credential) handled gracefully ───

def test_press_account_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No press account connected → send raises PressAccountNotConnected.
    monkeypatch.delenv("SIGNAL_BLASTER_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="send_press_pitch",
                      input={"outlet_id": "out-pitchfork", "subject": "Pitch",
                             "body": "Body"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a press account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "signal-blaster",
        "message":   "pitch my single to pitchfork",
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
    assert actions_evt["press_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "press_account_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_press_account_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("SIGNAL_BLASTER_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="send_press_pitch",
                      input={"outlet_id": "out-the-fader", "subject": "Pitch",
                             "body": "Body"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your press-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "signal-blaster",
        "message":   "pitch my single to the fader",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["press_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "press_account_auth_expired"
