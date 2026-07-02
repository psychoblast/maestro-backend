"""
PROOF tests — Aria (fan-builder) Anthropic tool_use loop.

Mirrors tests/test_wire_vault_keeper.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Aria emits search_fan_segments → build_engagement_campaign →
      schedule_fan_broadcast then a final message; all three mock-first
      fan_builder_service functions are invoked with the correct args and the
      stream surfaces a populated `actions` event (actions_taken), with
      FAN_BUILDER_TOOLS passed on every create() call;
  (b) a NON-fan agent (producer-connect) never receives FAN_BUILDER_TOOLS — it takes
      the unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never FAN_BUILDER_TOOLS;
  (d) the platform-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries fan_platform_not_connected=True);
  (e) expired platform auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / fan-CRM calls —
the Anthropic client is faked and the fan_builder_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-fan path."""
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


# ── (a) Aria runs the tool loop and surfaces actions_taken ───────────────────

def test_fan_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected fan platform so the broadcast succeeds (no network).
    monkeypatch.setenv("FAN_BUILDER_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) fan_builder_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, build_calls, bcast_calls = [], [], []
    real_search = m.fan_builder_service.search_fan_segments
    real_build  = m.fan_builder_service.build_engagement_campaign
    real_bcast  = m.fan_builder_service.schedule_fan_broadcast

    async def rec_search(segment_type="", tier=""):
        search_calls.append({"segment_type": segment_type, "tier": tier})
        return await real_search(segment_type=segment_type, tier=tier)

    async def rec_build(artist_id, segment_id="", campaign_name="", target_reach=0):
        build_calls.append({"artist_id": artist_id, "segment_id": segment_id,
                            "campaign_name": campaign_name, "target_reach": target_reach})
        return await real_build(artist_id, segment_id=segment_id,
                                campaign_name=campaign_name, target_reach=target_reach)

    async def rec_bcast(artist_id, channel, message, segment=""):
        bcast_calls.append({"artist_id": artist_id, "channel": channel,
                            "message": message, "segment": segment})
        return await real_bcast(artist_id, channel, message, segment)

    monkeypatch.setattr(m.fan_builder_service, "search_fan_segments",       rec_search)
    monkeypatch.setattr(m.fan_builder_service, "build_engagement_campaign", rec_build)
    monkeypatch.setattr(m.fan_builder_service, "schedule_fan_broadcast",    rec_bcast)

    # Scripted Anthropic responses: search → build → broadcast → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_fan_segments",
                      input={"segment_type": "superfans", "tier": "core"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="build_engagement_campaign",
                      input={"segment_id": "seg-superfans",
                             "campaign_name": "Album Drop", "target_reach": 10000}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_fan_broadcast",
                      input={"channel": "sms", "message": "New album out Friday!",
                             "segment": "seg-superfans"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found your superfans, built the campaign, and scheduled the broadcast.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Aria.
    def _no_stream(**kw):
        raise AssertionError("fan-builder must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "fan-builder",
        "message":   "rally my superfans for the album drop",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"segment_type": "superfans", "tier": "core"}], search_calls
    assert build_calls == [{
        "artist_id": "artist-9", "segment_id": "seg-superfans",
        "campaign_name": "Album Drop", "target_reach": 10000,
    }], build_calls
    assert bcast_calls == [{
        "artist_id": "artist-9", "channel": "sms",
        "message": "New album out Friday!", "segment": "seg-superfans",
    }], bcast_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_fan_segments", "build_engagement_campaign",
        "schedule_fan_broadcast",
    ], tools_used
    assert actions_evt["fan_platform_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "segment(s) found" in by_tool["search_fan_segments"]["result"]
    # name present, segment known, positive reach → viable / launch.
    assert "viable=True" in by_tool["build_engagement_campaign"]["result"]
    assert "launch" in by_tool["build_engagement_campaign"]["result"]
    assert by_tool["schedule_fan_broadcast"]["result"] == "broadcast scheduled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, build, broadcast, final.
    assert len(create_calls) == 4
    # FAN_BUILDER_TOOLS passed on every fan create call (never other toolsets).
    assert all(kw.get("tools") == m.FAN_BUILDER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VAULT_KEEPER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MERCH_EMPIRE_TOOLS for kw in create_calls)


# ── (b) Non-fan agent never gets fan tools, takes the unchanged path ──────────

def test_non_fan_agent_never_receives_fan_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT fan-builder, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-fan agent must not invoke the tool_use create loop"
    # No actions event for non-fan agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not fan tools ───────

def test_marcus_still_uses_marcus_tools_not_fan(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the fan gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.FAN_BUILDER_TOOLS


# ── (d) fan_platform_not_connected (missing credential) handled gracefully ────

def test_fan_platform_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No fan platform connected → schedule raises FanPlatformNotConnected.
    monkeypatch.delenv("FAN_BUILDER_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="schedule_fan_broadcast",
                      input={"channel": "email", "message": "Hi fans",
                             "segment": "seg-engaged"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a fan platform first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "fan-builder",
        "message":   "blast my engaged fans",
        "artist_id": "artist-no-platform",
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
    assert actions_evt["fan_platform_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "fan_platform_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_fan_platform_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("FAN_BUILDER_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="schedule_fan_broadcast",
                      input={"channel": "sms", "message": "We miss you",
                             "segment": "seg-lapsed"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your fan-platform auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "fan-builder",
        "message":   "win back my lapsed fans",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["fan_platform_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "fan_platform_auth_expired"
