"""
PROOF tests — Diego (design-studio) Anthropic tool_use loop.

Mirrors tests/test_wire_vision_forge.py / tests/test_marcus_tool_use.py. Proves
that, in /api/chat_stream:

  (a) Diego emits search_brand_styles → draft_brand_brief → produce_brand_asset then
      a final message; all three mock-first design_studio_service functions are
      invoked with the correct args and the stream surfaces a populated `actions`
      event (actions_taken), with DESIGN_STUDIO_TOOLS passed on every create() call;
  (b) a NON-design agent (producer-connect) never receives DESIGN_STUDIO_TOOLS — it takes the
      unchanged streaming path and emits NO `actions` event;
  (c) the gate is exclusive: Marcus (puppet-master) still runs its OWN tool loop
      with MARCUS_TOOLS, never DESIGN_STUDIO_TOOLS;
  (d) the workspace-not-connected (missing-credential) path is handled gracefully
      (no crash; the actions event carries design_workspace_not_connected=True);
  (e) expired workspace auth also degrades to the not-connected path.

Everything is in-process and deterministic. NO network / LLM / render calls — the
Anthropic client is faked and the design_studio_service boundary is exercised through
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
    """Stand-in for async_client.messages.stream(...) — used by the non-design path."""
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


# ── (a) Diego runs the tool loop and surfaces actions_taken ──────────────────

def test_design_tool_loop_invokes_functions_and_emits_actions(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # A connected design workspace so the asset production succeeds (no network).
    monkeypatch.setenv("DESIGN_STUDIO_ACCOUNT_CONNECTED", "true")

    # Record calls into the REAL (pure) design_studio_service functions, delegating
    # to the originals so we assert on real, deterministic output.
    search_calls, draft_calls, prod_calls = [], [], []
    real_search = m.design_studio_service.search_brand_styles
    real_draft  = m.design_studio_service.draft_brand_brief
    real_prod   = m.design_studio_service.produce_brand_asset

    async def rec_search(asset_type="", tier=""):
        search_calls.append({"asset_type": asset_type, "tier": tier})
        return await real_search(asset_type=asset_type, tier=tier)

    async def rec_draft(artist_id, concept="", asset_type="", tone=""):
        draft_calls.append({"artist_id": artist_id, "concept": concept,
                            "asset_type": asset_type, "tone": tone})
        return await real_draft(artist_id, concept=concept, asset_type=asset_type, tone=tone)

    async def rec_prod(artist_id, style_id, prompt, notes=""):
        prod_calls.append({"artist_id": artist_id, "style_id": style_id,
                           "prompt": prompt, "notes": notes})
        return await real_prod(artist_id, style_id, prompt, notes)

    monkeypatch.setattr(m.design_studio_service, "search_brand_styles", rec_search)
    monkeypatch.setattr(m.design_studio_service, "draft_brand_brief",   rec_draft)
    monkeypatch.setattr(m.design_studio_service, "produce_brand_asset", rec_prod)

    # Scripted Anthropic responses: search → draft → produce → final text.
    responses = [
        _Resp([_Block("tool_use", name="search_brand_styles",
                      input={"asset_type": "logo", "tier": "A"}, id="t1")], "tool_use"),
        _Resp([_Block("tool_use", name="draft_brand_brief",
                      input={"concept": "Bold monogram for a rising artist",
                             "asset_type": "logo",
                             "tone": "confident and timeless"}, id="t2")], "tool_use"),
        _Resp([_Block("tool_use", name="produce_brand_asset",
                      input={"style_id": "brd-monogram-serif", "prompt": "elegant serif monogram",
                             "notes": "dark and light lockups"}, id="t3")], "tool_use"),
        _Resp([_Block("text", text="Done — I found the style, drafted the brief, and produced your logo.")],
              "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)
    # Guard: the streaming path must NOT be used by Diego.
    def _no_stream(**kw):
        raise AssertionError("design-studio must not use messages.stream")
    monkeypatch.setattr(m.async_client.messages, "stream", _no_stream)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "design-studio",
        "message":   "find a logo style, draft a brief, and produce my brand mark",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # All three internal functions invoked with correct args.
    assert search_calls == [{"asset_type": "logo", "tier": "A"}], search_calls
    assert draft_calls == [{
        "artist_id": "artist-9", "concept": "Bold monogram for a rising artist",
        "asset_type": "logo",
        "tone": "confident and timeless",
    }], draft_calls
    assert prod_calls == [{
        "artist_id": "artist-9", "style_id": "brd-monogram-serif",
        "prompt": "elegant serif monogram",
        "notes": "dark and light lockups",
    }], prod_calls

    # actions event present, populated, before done.
    assert "actions" in types, types
    assert "done" in types
    assert types.index("actions") < types.index("done")
    actions_evt = next(e for e in events if e["type"] == "actions")
    tools_used  = [a["tool"] for a in actions_evt["actions_taken"]]
    assert tools_used == [
        "search_brand_styles", "draft_brand_brief", "produce_brand_asset",
    ], tools_used
    assert actions_evt["design_workspace_not_connected"] is False

    # Real, deterministic results surfaced in the action summaries.
    by_tool = {a["tool"]: a for a in actions_evt["actions_taken"]}
    assert "style(s) found" in by_tool["search_brand_styles"]["result"]
    # concept + asset_type present → drafted / produce.
    assert "drafted=True" in by_tool["draft_brand_brief"]["result"]
    assert "produce" in by_tool["draft_brand_brief"]["result"]
    assert by_tool["produce_brand_asset"]["result"] == "brand asset produced"

    assert "Done" in next(e for e in events if e["type"] == "done")["full_text"]
    # Four create() round-trips: search, draft, produce, final.
    assert len(create_calls) == 4
    # DESIGN_STUDIO_TOOLS passed on every design create call (never other toolsets).
    assert all(kw.get("tools") == m.DESIGN_STUDIO_TOOLS for kw in create_calls)
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
    assert all(kw.get("tools") != m.VISION_FORGE_TOOLS for kw in create_calls)


# ── (b) Non-design agent never gets design tools, takes the unchanged path ────

def test_non_design_agent_never_receives_design_tools(monkeypatch, tmp_path):
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
        "agent_id":  "collab-connect",   # NOT design-studio, NOT any tool-loop agent
        "message":   "give me a general check-in",
        "artist_id": "artist-9",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types  = [e["type"] for e in events]

    # Unchanged path: the tool-loop create() is never touched.
    assert create_calls == [], "non-design agent must not invoke the tool_use create loop"
    # No actions event for non-design agents.
    assert "actions" not in types, types
    assert "done" in types


# ── (c) Gate is exclusive: Marcus still uses MARCUS_TOOLS, not design tools ────

def test_marcus_still_uses_marcus_tools_not_design(monkeypatch, tmp_path):
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
    # Marcus keeps its own toolset — the design gate did not bleed into it.
    assert create_calls[0].get("tools") == m.MARCUS_TOOLS
    assert create_calls[0].get("tools") != m.DESIGN_STUDIO_TOOLS


# ── (d) design_workspace_not_connected (missing credential) handled gracefully ─

def test_design_workspace_not_connected_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    # No design workspace connected → produce raises DesignWorkspaceNotConnected.
    monkeypatch.delenv("DESIGN_STUDIO_ACCOUNT_CONNECTED", raising=False)

    responses = [
        _Resp([_Block("tool_use", name="produce_brand_asset",
                      input={"style_id": "brd-monogram-serif", "prompt": "logo",
                             "notes": "n"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="You need to connect a design workspace first.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "design-studio",
        "message":   "produce my logo",
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
    assert actions_evt["design_workspace_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "design_workspace_not_connected"


# ── (e) expired auth also degrades to the not-connected path ─────────────────

def test_design_workspace_auth_expired_is_handled(monkeypatch, tmp_path):
    m = _load_main(monkeypatch, tmp_path)

    monkeypatch.setenv("DESIGN_STUDIO_ACCOUNT_CONNECTED", "expired")

    responses = [
        _Resp([_Block("tool_use", name="produce_brand_asset",
                      input={"style_id": "brd-bold-wordmark", "prompt": "wordmark",
                             "notes": "n"}, id="t1")], "tool_use"),
        _Resp([_Block("text", text="Your design-workspace auth expired.")], "end_turn"),
    ]
    create_calls = []

    async def fake_create(**kwargs):
        create_calls.append(kwargs)
        return responses[len(create_calls) - 1]

    monkeypatch.setattr(m.async_client.messages, "create", fake_create)

    client = TestClient(m.app)
    resp = client.post("/api/chat_stream", json={
        "agent_id":  "design-studio",
        "message":   "produce my wordmark",
        "artist_id": "artist-expired",
        "history":   "[]",
        "tts":       False,
    })
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    actions_evt = next(e for e in events if e["type"] == "actions")
    assert actions_evt["design_workspace_not_connected"] is True
    assert actions_evt["actions_taken"][0]["result"] == "design_workspace_auth_expired"
