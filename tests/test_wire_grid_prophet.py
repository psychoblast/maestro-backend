"""
PROOF tests — Kai (grid-prophet) Anthropic tool_use loop.

Mirrors tests/test_wire_signal_blaster.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Kai emits search_growth_channels → draft_content_plan → schedule_post then a
      final message; all three mock-first grid_prophet_service functions are invoked
      with the correct args and the stream surfaces a populated `actions` event
      (actions_taken), with GRID_PROPHET_TOOLS passed on every create() call;
  (b) a NON-grid agent (producer-connect) never receives GRID_PROPHET_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never GRID_PROPHET_TOOLS;
  (d) the account-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries social_account_not_connected=True);
  (e) expired account auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / social calls — the
Anthropic client is faked and the grid_prophet_service boundary is exercised through
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
    """Stand-in for async_client.messages.stream(...) — used by the non-grid path."""
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


# ── (a) Kai runs the tool loop and surfaces actions_taken ────────────────────

def test_grid_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected social account so the post schedule succeeds (no network).
    monkeypatch.setenv("GRID_PROPHET_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) grid_prophet_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, draft_calls, post_calls = [], [], []
    real_search = m.grid_prophet_service.search_growth_channels
    real_draft  = m.grid_prophet_service.draft_content_plan
    real_post   = m.grid_prophet_service.schedule_post

    async def rec_search(platform="", tier=""):
        search_calls.append({"platform": platform, "tier": tier})
        return await real_search(platform=platform, tier=tier)

    async def rec_draft(artist_id, hook="", platform="", cadence=""):
        draft_calls.append({"artist_id": artist_id, "hook": hook,
                            "platform": platform, "cadence": cadence})
        return await real_draft(artist_id, hook=hook, platform=platform, cadence=cadence)

    async def rec_post(artist_id, channel_id, caption, body=""):
        post_calls.append({"artist_id": artist_id, "channel_id": channel_id,
                           "caption": caption, "body": body})
        return await real_post(artist_id, channel_id, caption, body)

    monkeypatch.setattr(m.grid_prophet_service, "search_growth_channels", rec_search)
    monkeypatch.setattr(m.grid_prophet_service, "draft_content_plan",     rec_draft)
    monkeypatch.setattr(m.grid_prophet_service, "schedule_post",          rec_post)

    # Scripted Anthropic responses: search → draft → schedule → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_growth_channels",
                      input={"platform": "tiktok", "tier": "A"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_content_plan",
                      input={"hook": "Behind the scenes of the new single",
                             "platform": "TikTok",
                             "cadence": "3x per week"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_post",
                      input={"channel_id": "ch-tiktok", "caption": "New single out now",
                             "body": "Full clip in bio."}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the channel, drafted the plan, and scheduled your post.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Kai.
    def _no_stream(**kw):
        raise AssertionError("grid-prophet must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "grid-prophet",
        "message":   "find a tiktok channel, draft a plan, and schedule my post",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"platform": "tiktok", "tier": "A"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "hook": "Behind the scenes of the new single",
        "platform": "TikTok",
        "cadence": "3x per week",
    }], draft_calls
    assert post_calls == [{
        "artist_id": "artist-9", "channel_id": "ch-tiktok",
        "caption": "New single out now",
        "body": "Full clip in bio.",
    }], post_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_growth_channels", "draft_content_plan", "schedule_post",
    ], tools_used
    assert actions_evt["social_account_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "channel(s) found" in by_tool["search_growth_channels"]["result"]
    # hook + platform present → drafted / publish.
    assert "drafted=True" in by_tool["draft_content_plan"]["result"]
    assert "publish" in by_tool["draft_content_plan"]["result"]
    assert by_tool["schedule_post"]["result"] == "post scheduled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, schedule, final.
    assert len(create_calls) == 4
    # GRID_PROPHET_TOOLS passed on every grid create call (never other toolsets).
    assert all(kw.get("tools") == m.GRID_PROPHET_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.FUND_PHANTOM_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.RIGHTS_PULSE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.BORDER_ROYALTY_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MECH_LEDGER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VAULT_KEEPER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEDGER_LOCK_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.SIGNAL_BLASTER_TOOLS for kw in create_calls)


# ── (b) Non-grid agent never gets grid tools, takes the unchanged path ────────

def test_non_grid_agent_never_receives_grid_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT grid-prophet, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-grid agent must not invoke the tool_use create loop"
    # No actions event for non-grid agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not grid tools ──────

def test_marcus_still_uses_marcus_tools_not_grid(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the grid gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.GRID_PROPHET_TOOLS


# ── (d) social_account_not_connected (missing credential) handled gracefully ──

def test_social_account_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No social account connected → schedule raises SocialAccountNotConnected.
    monkeypatch.delenv("GRID_PROPHET_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="schedule_post",
                      input={"channel_id": "ch-tiktok", "caption": "Pitch",
                             "body": "Body"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a social account first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "grid-prophet",
        "message":   "schedule my post on tiktok",
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
    assert actions_evt["social_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "social_account_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_social_account_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("GRID_PROPHET_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="schedule_post",
                      input={"channel_id": "ch-reels", "caption": "Pitch",
                             "body": "Body"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your social-account auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "grid-prophet",
        "message":   "schedule my post on reels",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["social_account_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "social_account_auth_expired"
