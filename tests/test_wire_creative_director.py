"""
PROOF tests — Cree (creative-director) Anthropic tool_use loop.

Mirrors tests/test_wire_sync_agent.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Cree emits search_rollout_templates → assess_creative_concept →
      schedule_rollout then a final message; all three mock-first
      creative_director_service functions are invoked with the correct args and
      the stream surfaces a populated `actions` event (actions_taken), with
      CREATIVE_DIRECTOR_TOOLS passed on every create() call;
  (b) a NON-creative-director agent (producer-connect) never receives
      CREATIVE_DIRECTOR_TOOLS — it takes the unchanged streaming path and emits
      NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never CREATIVE_DIRECTOR_TOOLS;
  (d) the studio-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries creative_studio_not_connected=True);
  (e) expired studio auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM calls — the
Anthropic client is faked and the creative_director_service boundary is exercised
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
    """Stand-in for async_client.messages.stream(...) — used by the non-Cree path."""
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


# ── (a) Cree runs the tool loop and surfaces actions_taken ───────────────────

def test_creative_director_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected creative studio so the rollout succeeds (no network).
    monkeypatch.setenv("CREATIVE_DIRECTOR_STUDIO_CONNECTED", "true")

    # Record calls into the REAL (pure) creative_director_service functions,
    # delegating to the originals so we assert on real, deterministic output.
    search_calls, assess_calls, schedule_calls = [], [], []
    real_search   = m.creative_director_service.search_rollout_templates
    real_assess   = m.creative_director_service.assess_creative_concept
    real_schedule = m.creative_director_service.schedule_rollout

    async def rec_search(release_type="", goal=""):
        search_calls.append({"release_type": release_type, "goal": goal})
        return await real_search(release_type=release_type, goal=goal)

    async def rec_assess(artist_id, template_id="", release_title="", theme="",
                         weeks_to_release=0, has_visual_assets=False):
        assess_calls.append({"artist_id": artist_id, "template_id": template_id,
                             "release_title": release_title, "theme": theme,
                             "weeks_to_release": weeks_to_release,
                             "has_visual_assets": has_visual_assets})
        return await real_assess(artist_id, template_id=template_id,
                                 release_title=release_title, theme=theme,
                                 weeks_to_release=weeks_to_release,
                                 has_visual_assets=has_visual_assets)

    async def rec_schedule(artist_id, template_id, release_title, kickoff=""):
        schedule_calls.append({"artist_id": artist_id, "template_id": template_id,
                               "release_title": release_title, "kickoff": kickoff})
        return await real_schedule(artist_id, template_id, release_title, kickoff)

    monkeypatch.setattr(m.creative_director_service, "search_rollout_templates", rec_search)
    monkeypatch.setattr(m.creative_director_service, "assess_creative_concept",  rec_assess)
    monkeypatch.setattr(m.creative_director_service, "schedule_rollout",         rec_schedule)

    # Scripted Anthropic responses: search → assess → schedule → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_rollout_templates",
                      input={"release_type": "album", "goal": "press"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="assess_creative_concept",
                      input={"template_id": "tpl-album-era-launch",
                             "release_title": "Nightfall", "theme": "cinematic",
                             "weeks_to_release": 12, "has_visual_assets": True}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="schedule_rollout",
                      input={"template_id": "tpl-album-era-launch",
                             "release_title": "Nightfall", "kickoff": "next monday"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found a template, assessed your concept, and scheduled the rollout.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Cree.
    def _no_stream(**kw):
        raise AssertionError("creative-director must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "creative-director",
        "message":   "plan an album press rollout and schedule it",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"release_type": "album", "goal": "press"}], search_calls
    assert assess_calls == [{
        "artist_id": "artist-9", "template_id": "tpl-album-era-launch",
        "release_title": "Nightfall", "theme": "cinematic",
        "weeks_to_release": 12, "has_visual_assets": True,
    }], assess_calls
    assert schedule_calls == [{
        "artist_id": "artist-9", "template_id": "tpl-album-era-launch",
        "release_title": "Nightfall", "kickoff": "next monday",
    }], schedule_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_rollout_templates", "assess_creative_concept", "schedule_rollout",
    ], tools_used
    assert actions_evt["creative_studio_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "template(s) found" in by_tool["search_rollout_templates"]["result"]
    # theme + timing-in-window + assets present → ready / proceed.
    assert "ready=True" in by_tool["assess_creative_concept"]["result"]
    assert "proceed" in by_tool["assess_creative_concept"]["result"]
    assert by_tool["schedule_rollout"]["result"] == "rollout scheduled"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, assess, schedule, final.
    assert len(create_calls) == 4
    # CREATIVE_DIRECTOR_TOOLS passed on every Cree create call (never other toolsets).
    assert all(kw.get("tools") == m.CREATIVE_DIRECTOR_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.SYNC_AGENT_TOOLS for kw in create_calls)


# ── (b) Non-Cree agent never gets Cree tools, takes the unchanged path ────────

def test_non_creative_director_agent_never_receives_cree_tools(monkeypatch, tmp_path):
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
        "agent_id":  "music-edu",   # NOT creative-director, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-Cree agent must not invoke the tool_use create loop"
    # No actions event for non-Cree agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not Cree tools ──────

def test_marcus_still_uses_marcus_tools_not_creative_director(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the Cree gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.CREATIVE_DIRECTOR_TOOLS


# ── (d) creative_studio_not_connected (missing credential) handled gracefully ─

def test_creative_studio_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No creative studio connected → schedule raises CreativeStudioNotConnected.
    monkeypatch.delenv("CREATIVE_DIRECTOR_STUDIO_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="schedule_rollout",
                      input={"template_id": "tpl-single-slow-burn",
                             "release_title": "Quiet Hours"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a creative studio first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "creative-director",
        "message":   "schedule my single rollout",
        "artist_id": "artist-no-studio",
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
    assert actions_evt["creative_studio_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "creative_studio_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_creative_studio_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("CREATIVE_DIRECTOR_STUDIO_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="schedule_rollout",
                      input={"template_id": "tpl-ep-story-arc",
                             "release_title": "Rise"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your creative-studio auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "creative-director",
        "message":   "schedule my EP rollout",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["creative_studio_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "creative_studio_auth_expired"
