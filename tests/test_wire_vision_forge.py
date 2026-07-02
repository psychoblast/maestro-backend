"""
PROOF tests — Luna (vision-forge) Anthropic tool_use loop.

Mirrors tests/test_wire_grid_prophet.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Luna emits search_visual_styles → draft_visual_brief → generate_artwork then a
      final message; all three mock-first vision_forge_service functions are invoked
      with the correct args and the stream surfaces a populated `actions` event
      (actions_taken), with VISION_FORGE_TOOLS passed on every create() call;
  (b) a NON-vision agent (producer-connect) never receives VISION_FORGE_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never VISION_FORGE_TOOLS;
  (d) the workspace-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries render_workspace_not_connected=True);
  (e) expired workspace auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / render calls — the
Anthropic client is faked and the vision_forge_service boundary is exercised through
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
    """Stand-in for async_client.messages.stream(...) — used by the non-vision path."""
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


# ── (a) Luna runs the tool loop and surfaces actions_taken ───────────────────

def test_vision_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected render workspace so the artwork generation succeeds (no network).
    monkeypatch.setenv("VISION_FORGE_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) vision_forge_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, draft_calls, gen_calls = [], [], []
    real_search = m.vision_forge_service.search_visual_styles
    real_draft  = m.vision_forge_service.draft_visual_brief
    real_gen    = m.vision_forge_service.generate_artwork

    async def rec_search(medium="", tier=""):
        search_calls.append({"medium": medium, "tier": tier})
        return await real_search(medium=medium, tier=tier)

    async def rec_draft(artist_id, concept="", medium="", palette=""):
        draft_calls.append({"artist_id": artist_id, "concept": concept,
                            "medium": medium, "palette": palette})
        return await real_draft(artist_id, concept=concept, medium=medium, palette=palette)

    async def rec_gen(artist_id, style_id, prompt, notes=""):
        gen_calls.append({"artist_id": artist_id, "style_id": style_id,
                          "prompt": prompt, "notes": notes})
        return await real_gen(artist_id, style_id, prompt, notes)

    monkeypatch.setattr(m.vision_forge_service, "search_visual_styles", rec_search)
    monkeypatch.setattr(m.vision_forge_service, "draft_visual_brief",   rec_draft)
    monkeypatch.setattr(m.vision_forge_service, "generate_artwork",     rec_gen)

    # Scripted Anthropic responses: search → draft → generate → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_visual_styles",
                      input={"medium": "cover_art", "tier": "A"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_visual_brief",
                      input={"concept": "Neon skyline at dusk",
                             "medium": "cover_art",
                             "palette": "magenta and teal"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="generate_artwork",
                      input={"style_id": "sty-neon-noir", "prompt": "moody neon skyline cover",
                             "notes": "portrait crop"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the style, drafted the brief, and generated your artwork.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Luna.
    def _no_stream(**kw):
        raise AssertionError("vision-forge must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "vision-forge",
        "message":   "find a cover art style, draft a brief, and generate my artwork",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"medium": "cover_art", "tier": "A"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "concept": "Neon skyline at dusk",
        "medium": "cover_art",
        "palette": "magenta and teal",
    }], draft_calls
    assert gen_calls == [{
        "artist_id": "artist-9", "style_id": "sty-neon-noir",
        "prompt": "moody neon skyline cover",
        "notes": "portrait crop",
    }], gen_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_visual_styles", "draft_visual_brief", "generate_artwork",
    ], tools_used
    assert actions_evt["render_workspace_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "style(s) found" in by_tool["search_visual_styles"]["result"]
    # concept + medium present → drafted / produce.
    assert "drafted=True" in by_tool["draft_visual_brief"]["result"]
    assert "produce" in by_tool["draft_visual_brief"]["result"]
    assert by_tool["generate_artwork"]["result"] == "artwork generated"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, generate, final.
    assert len(create_calls) == 4
    # VISION_FORGE_TOOLS passed on every vision create call (never other toolsets).
    assert all(kw.get("tools") == m.VISION_FORGE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MARCUS_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEX_CIPHER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.FUND_PHANTOM_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.RIGHTS_PULSE_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.BORDER_ROYALTY_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.MECH_LEDGER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.VAULT_KEEPER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.LEDGER_LOCK_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.SIGNAL_BLASTER_TOOLS for kw in create_calls)
    assert all(kw.get("tools") != m.GRID_PROPHET_TOOLS for kw in create_calls)


# ── (b) Non-vision agent never gets vision tools, takes the unchanged path ────

def test_non_vision_agent_never_receives_vision_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT vision-forge, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-vision agent must not invoke the tool_use create loop"
    # No actions event for non-vision agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not vision tools ────

def test_marcus_still_uses_marcus_tools_not_vision(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the vision gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.VISION_FORGE_TOOLS


# ── (d) render_workspace_not_connected (missing credential) handled gracefully ─

def test_render_workspace_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No render workspace connected → generate raises RenderWorkspaceNotConnected.
    monkeypatch.delenv("VISION_FORGE_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="generate_artwork",
                      input={"style_id": "sty-neon-noir", "prompt": "cover",
                             "notes": "n"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a render workspace first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "vision-forge",
        "message":   "generate my cover art",
        "artist_id": "artist-no-workspace",
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
    assert actions_evt["render_workspace_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "render_workspace_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_render_workspace_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("VISION_FORGE_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="generate_artwork",
                      input={"style_id": "sty-analog-film", "prompt": "cover",
                             "notes": "n"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your render-workspace auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "vision-forge",
        "message":   "generate my cover art",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["render_workspace_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "render_workspace_auth_expired"
